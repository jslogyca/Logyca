# -*- coding: utf-8 -*-

{
    'name': 'l10n COL Payroll',
    'summary': 'l10n COL Payroll',
    'version': '1.1',
    'category': 'Human Resources/Employees',
    'website': 'https://logyca.com',
    'author': 'LOGYCA / SERVICIOS SAS',
    'license': '',
    'support': 'lctorres@logyca.com',
    'maintainer': 'LOGYCA / SERVICIOS SAS',
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'hr',
        'hr_payroll',
        'hr_payroll_account',
    ],
    'description': '''

========================

''',    
    'data': [
        # 'security/security.xml',
        # 'security/ir.model.access.csv',
        'views/hr_payslip_input_type_view.xml',
        'views/hr_payslip_view.xml',
    ],
    'qweb': [
    ]
}
