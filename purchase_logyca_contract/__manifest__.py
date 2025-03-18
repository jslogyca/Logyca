# -*- coding: utf-8 -*-

{
    'name': 'Purchase Logyca',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'account',
        'purchase',
        'base',
        'purchase_blanket_order',
        'purchase_order_type',
        ],
    'description': '''

========================

''',    
    'data': [
        'views/purchase_blanket_order_view.xml',
    ],
    'qweb': [
    ]
}
