{
    'name': 'Community_application',
    'version': '1.0',
    'license': 'LGPL-3',
    'summary': 'Social Media Module for posting images and videos',
    'sequence': 10,
    'description': """Social Media Module for Odoo 14""",
    'category': 'Tools',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/post_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
