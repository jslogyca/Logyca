# -*- coding: utf-8 -*-

{
    'name': 'Payroll Account',
    'summary': 'Payroll Account',
    'version': '1.1',
    'category': 'Human Resources/Employees',
    'website': 'https://logyca.com',
    'author': 'LOGYCA / SERVICIOS SAS',
    'license': 'LGPL-3',
    'support': 'lctorres@logyca.com',
    'maintainer': 'LOGYCA / SERVICIOS SAS',
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'hr',
        'hr_payroll',
        'logyca',
    ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_account_config_view.xml',
        'views/hr_payslip_run_view.xml',
        'views/hr_payroll_account_ss_view.xml',
        'views/hr_employee.xml',
    ],
    'qweb': [
    ]
}
