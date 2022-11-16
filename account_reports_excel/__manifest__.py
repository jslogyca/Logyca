# -*- coding: utf-8 -*-

{
    'name': 'Report Excel Account',
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
        'sale',
        'web_tree_many2one_clickable',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/report_excel_sale_product_wizard_view.xml',
        'wizard/account_income_report_wizard_view.xml',
        'report/account_income_report_view.xml',
        'report/report_excel_sale_product_view.xml',
        'report/report_excel_enforcement_view.xml',
    ],
    'qweb': [
    ]
}
