from odoo import models, fields, api


class DocumentsDocument(models.Model):
    _inherit = 'documents.document'
    
    # 添加隐藏的公司字段，用于多公司过滤
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        compute='_compute_company_id',
        store=True,
        index=True,
        recursive=True,
        help="Company of the document based on its folder hierarchy"
    )
    
    def _get_folder_company(self, folder):
        """递归向上查找文件夹的公司配置"""
        if not folder:
            return False
        
        # 检查是否是系统创建的文件夹
        if self._is_system_folder(folder):
            return False
        
        if folder.company_id:
            return folder.company_id
        
        # 如果当前文件夹没有公司配置，向上查找父文件夹
        return self._get_folder_company(folder.folder_id)
    
    def _is_system_folder(self, folder):
        """判断是否是系统创建的文件夹"""
        if not folder:
            return False
        
        # 检查是否有XML ID（系统创建的通常有XML ID）
        try:
            data = self.env['ir.model.data'].sudo().search([
                ('model', '=', 'documents.document'),
                ('res_id', '=', folder.id)
            ], limit=1)
            
            if data:
                return True
        except Exception:
            # 如果访问失败，继续使用其他方法判断
            pass
        
        # 检查是否是系统默认的文件夹名称
        system_folder_names = ['Inbox', 'Internal', 'Workspace', 'Finance', 'HR', 'Projects']
        if folder.name in system_folder_names and not folder.folder_id:
            return True
            
        return False
    
    @api.depends('folder_id', 'folder_id.company_id')
    def _compute_company_id(self):
        """根据文件夹的公司设置计算文件的公司，支持向上查找"""
        for document in self:
            if document.folder_id:
                # 沿着文件夹层级向上查找公司配置
                company = self._get_folder_company(document.folder_id)
                if company:
                    document.company_id = company
                else:
                    # 如果整个文件夹层级都没有公司限制或是系统文件夹，使用False表示所有公司都可以访问
                    document.company_id = False
            else:
                # 如果没有文件夹，使用False表示所有公司都可以访问
                document.company_id = False
    
    @api.model_create_multi
    def create(self, vals_list):
        """创建文档时自动设置公司"""
        documents = super().create(vals_list)
        # 触发计算字段更新
        documents._compute_company_id()
        return documents
    
    def write(self, vals):
        """更新文档时检查是否需要重新计算公司"""
        # 避免递归调用
        if self.env.context.get('skip_company_recompute'):
            return super().write(vals)
            
        result = super().write(vals)
        
        # 只有在folder_id发生变化时才重新计算公司，避免递归
        if 'folder_id' in vals:
            # 如果这是一个文件夹（is_folder=True），需要更新其子文档的公司
            folders = self.filtered('is_folder')
            if folders:
                child_documents = self.env['documents.document'].search([
                    ('folder_id', 'in', folders.ids)
                ])
                if child_documents:
                    child_documents.with_context(skip_company_recompute=True)._compute_company_id()
                    
        return result
    
    def _get_permission_without_token(self):
        """重写权限检查方法，修复共享文件的公司权限问题"""
        self.ensure_one()
        is_user_company = self.company_id and self.company_id in self.env.user.company_ids
        is_disabled_company = is_user_company and self.company_id not in self.env.companies
        if is_disabled_company:
            return 'none'

        # own documents
        if self.owner_id == self.env.user:
            return 'edit'

        user_permission = 'none'
        # access with <documents.access>
        if access := self.access_ids.filtered(
            lambda a: a.partner_id == self.env.user.partner_id
            and (not a.expiration_date or a.expiration_date > fields.Datetime.now())
        ):
            user_permission = access.role or self.access_via_link

        # access as internal
        if not self.env.user.share and user_permission != "edit" and self.access_internal != 'none':
            # 修复：如果用户通过documents.access明确获得了权限，忽略公司限制
            has_explicit_access = self.access_ids.filtered(
                lambda a: a.partner_id == self.env.user.partner_id
                and (not a.expiration_date or a.expiration_date > fields.Datetime.now())
            )
            
            if has_explicit_access or not self.company_id or self.company_id in self.env.companies:
                user_permission = (
                    'edit' if self.env.user.has_group('documents.group_documents_manager')
                    else self.access_internal
                )

        return user_permission