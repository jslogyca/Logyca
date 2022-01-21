# -*- coding: utf-8 -*-

{
    'name': 'l10n COL Loan Management',
    'version': '14.0.1.0.0',
    'summary': 'Manage Loan Human Resources',
    'description': """
        Helps you to manage Loan Human Resources of your company's staff.
        """,
    "category": "Human Resources",
    'website': 'https://logyca.com',
    'author': 'LOGYCA / SERVICIOS SAS',
    'license': '',
    'support': 'lctorres@logyca.com',
    'maintainer': 'LOGYCA / SERVICIOS SAS',
    'depends': [
        'base', 
        'hr_payroll', 
        'hr',
        'l10n_co_lg_payroll',
    ],
    'data': [
        'views/hr_loan_seq.xml',
        'views/hr_loan_view.xml',
        'views/hr_loan_line_view.xml',
        'views/hr_employee_view.xml',
        'wizard/hr_loan_mass_wizard_view.xml',
        'security/ir.model.access.csv',
        'security/security.xml',        
    ],
    'qweb': [
    ]
}