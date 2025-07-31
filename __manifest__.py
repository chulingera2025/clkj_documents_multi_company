{
    'name': 'Documents Multi-Company',
    'version': '18.0.1.0.0',
    'category': 'Productivity/Documents',
    'summary': '实现文档模块的多公司文件权限隔离',
    'description': """
        此模块为Odoo文档模块添加多公司支持，实现文件级别的公司权限隔离。
        
        让文档模块的首页文件按照所在目录的公司配置显示，确保用户只能看到
        属于自己公司的文件，同时保持文件夹的原有公司隔离逻辑。
        
        - 文件按照其所在目录的公司配置进行过滤
        - 用户只能看到自己公司的文件
        - 文件夹的公司隔离保持原有逻辑不变
        - 支持无公司限制的公共文件夹
        - 自动应用多公司环境的权限规则
        
        1. 如果已安装项目模块，请先卸载项目模块
        2. 安装此文档多公司模块
        3. 安装完成后可重新安装项目模块
        
        ！！！注意：项目模块与此模块存在约束冲突，需要按上述顺序安装。！！！
        
        OCA是Odoo社区组织，致力于开发高质量的开源Odoo模块。
    """,
    'author': 'chulingera2025, OCA',
    'website': 'https://github.com/chulingera2025',
    'depends': [
        'documents',
    ],
    'data': [
        'security/ir_rule.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
    'maintainers': ['chulingera2025'],
    'external_dependencies': {},
}