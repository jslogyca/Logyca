# -*- coding: utf-8 -*-

{
    'name': 'Expense Extended LOGYCA',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'hr_expense',
        'logyca',
        ],
    'description': '''

========================

''',    
    'data': [
        # 'security/account_move_extended_security.xml',
        # 'security/ir.model.access.csv',
        'views/hr_expense_view.xml',
        # 'views/report_certification.xml',
        # 'views/revenue_macro_sector_view.xml',
        # 'views/product_template_view.xml',
        # 'views/res_users_view.xml',
        # 'views/account_move.xml',
        # 'views/account_sector_macro_view.xml',
        # 'views/res_partner_view.xml',
        # 'wizard/update_revenue_wizard_view.xml',
        # 'data/macrosectors_data.xml',
        # 'data/debtor_portfolio_status_data.xml'
    ],
    'qweb': [
    ]
}
