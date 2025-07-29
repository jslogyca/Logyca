# -*- coding: utf-8 -*-

{
    'name': 'Purchase Blanket Orders LOGYCA ',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'purchase_blanket_order',
        'logyca',
        'analytic',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_blanket_order_type_data.xml',
        'views/purchase_blanket_order_view.xml',
        'views/purchase_order_view.xml',
        'wizard/create_purchase_orders.xml',
    ],
    'qweb': [
    ]
}
