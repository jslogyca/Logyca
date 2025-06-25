# -*- coding: utf-8 -*-

{
    'name': 'MEMBERS - LOGYCA ',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'logyca',
        'contacts',
        'sale',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'wizard/member_tyb_wizard_view.xml',
    ],
    'qweb': [
    ]
}
