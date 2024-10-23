# -*- coding: utf-8 -*-

{
    'name': 'l10n COL Payroll',
    'summary': 'l10n COL Payroll',
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
        'hr_payroll_account',
        'hr_holidays',
        'hr_work_entry_contract_enterprise',
    ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',        
        'views/hr_payslip_input_type_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_salary_rule_view.xml',
        'views/hr_payslip_line_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_risk_view.xml',
        'views/res_company_view.xml',
        'views/resource_calendar_view.xml',
        'views/hr_leave_type_view.xml',
        'views/hr_prima_report.xml',
        'views/hr_reason_end_contract_view.xml',
        'views/hr_payroll_structure_view.xml',
    ],
    'qweb': [
    ]
}
