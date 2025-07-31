from . import models

def post_init_hook(env):
    """模块安装后的初始化钩子"""
    # 为现有的文档设置公司字段
    documents = env['documents.document'].with_context(skip_company_filter=True).search([])
    documents._compute_company_id()