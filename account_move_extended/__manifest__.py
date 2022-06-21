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
        'views/account_sector_red_view.xml',
        #'views/res_partner_view.xml',
        'views/revenue_macro_sector_view.xml',
        'views/product_template_view.xml',
        'views/res_users_view.xml',
        'views/account_move.xml',
        'views/account_sector_macro_view.xml',
        'wizard/update_revenue_wizard_view.xml',
        'security/ir.model.access.csv',
        'security/account_move_extended_security.xml',
        'data/macrosectors_data.xml',
        'data/debtor_portfolio_status_data.xml'
    ],
    'qweb': [
    ]
}
