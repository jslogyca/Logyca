# -*- coding: utf-8 -*-

{
    'name': 'Account Move Extended',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'account',
        'analytic',
        'logyca',
        ],
    'description': '''

========================

''',    
    'data': [
        'data/data.xml',
        'views/account_sector_red_view.xml',
        'views/res_partner_view.xml',
        'views/revenue_macro_sector_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [
    ]
}
