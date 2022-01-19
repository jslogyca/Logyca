# -*- coding: utf-8 -*-

{
    'name': 'Payroll Report',
    'summary': 'Payroll Report',
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
    ],
    'description': '''

========================

''',    
    'data': [
        'wizard/hr_payroll_report_view.xml',
        'security/ir.model.access.csv',
        'views/hr_salary_rule_view.xml',
        # 'views/report_payslip.xml',
        # 'report/hr_payslip_contractor_report.xml',
        # 'report/report_payslip_contractor.xml',
        # 'report/hr_payslip_report_contractor_invoice.xml',
        # 'report/report_contractor_invoice.xml'      
    ],
    'qweb': [
    ]
}
