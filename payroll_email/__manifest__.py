# -*- coding: utf-8 -*-

{
    'name': 'Payroll Email/Mass E-mail',
    'version': '1.1',
    'summary': """Payroll Email/Mass E-mail""",
    'description': 'This module helps you to send payslip through Email.',
    'category': 'Generic Modules/Human Resources',
    'author': 'LOGYCA / SERVICIOS SAS',
    'website': 'https://logyca.com',
    'license': 'LGPL-3',
    'support': 'lctorres@logyca.com',
    'maintainer': 'LOGYCA / SERVICIOS SAS',
    'application': False,
    'installable': True,    
    'depends': [
        'base', 
        'hr_payroll', 
        'mail', 
        'hr'
    ],
    'data': [
        # 'data/mail_template.xml',
        'security/ir.model.access.csv',
        'views/hr_payroll.xml',
        'views/hr_employee_view.xml',
        # 'views/hr_payslip_run_view.xml',
        'wizard/hr_payslip_wizard_view.xml',
        'wizard/hr_mass_payroll_wizard.xml',
    ],
    'qweb': [
    ]
}
