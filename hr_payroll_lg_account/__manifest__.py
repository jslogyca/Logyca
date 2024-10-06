# -*- coding: utf-8 -*-

{
    'name': 'LG Payroll Account',
    'summary': 'LG Payroll Account',
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
        'logyca',
        'hr_work_entry_contract_enterprise',
    ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'views/hr_salary_rule_view.xml',
        'views/account_analytic_type_view.xml',
        'views/logyca_budget_group_view.xml',
        'views/hr_employee_view.xml',
        'views/res_partner_view.xml',
    ],
    'qweb': [
    ]
}
