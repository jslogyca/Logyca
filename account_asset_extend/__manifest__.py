# -*- coding: utf-8 -*-

{
    'name': 'Account Asset Extend',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA SERVICIOS',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'account_asset',
        'account_move_extended',
        ],
    'description': '''

======================== Asset LOGYCA

''',    
    'data': [
        'views/account_asset_view.xml',
    ],
    'qweb': [
    ]
}
