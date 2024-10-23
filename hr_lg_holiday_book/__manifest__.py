# -*- coding: utf-8 -*-

{
    'name': 'LG Holiday Book',
    'summary': 'LG Holiday Book',
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
        'hr_holidays',
    ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/hr_holiday_book_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_leave_view.xml',
        'views/hr_leave_type_view.xml',
        'views/hr_holiday_book_ajust_view.xml',
        'wizard/hr_holiday_book_report_wizard_view.xml',
    ],
    'qweb': [
    ]
}
