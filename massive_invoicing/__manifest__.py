# -*- coding: utf-8 -*-

{
    'name': 'Massive Invoicing Logyca',
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
        'account_move_extended',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/massive_income_tariff_view.xml',
        # 'views/res_partner_view.xml',
        # 'views/massive_income_tariff_discounts_view.xml',
        # 'data/massive_income_tariff_data.xml',
    ],
    'qweb': [
    ]
}
