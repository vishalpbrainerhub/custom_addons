{
    'name': 'Rewards',
    'version': '1.0',
    'summary': 'Get rewards on order',
    'sequence': 10,
    'description': """Get rewards on order using Odoo 15""",
    'category': 'Tools',
    'depends': ['base', 'product', 'sale'],  # Added 'sale' as a dependency
    'data': [
        'security/ir.model.access.csv',
        'views/rewards.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
