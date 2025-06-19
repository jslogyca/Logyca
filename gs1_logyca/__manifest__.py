# -*- coding: utf-8 -*-

{
    'name': 'GS1 - LOGYCA ',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'crm',
        'contacts',
        'sale_management',
        ],
    'description': '''

========================

''',    
    'data': [
        'views/res_partner_view.xml',
        'views/sale_order_template_view.xml',
        # 'views/crm_team_view.xml',
    ],
    'qweb': [
    ]
}
