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
        data = self.env['ir.model.data'].search([
            ('model', '=', 'documents.document'),
            ('res_id', '=', folder.id)
        ], limit=1)
        
        if data:
            return True
        
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