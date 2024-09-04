{
    'name': 'products and order',
    'version': '1.0',
    'summary': 'products and order',
    'sequence': 10,
    'description': """products and order for Odoo 15""",
    'category': 'Tools',
    'depends': ['base', 'product','sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/post_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
