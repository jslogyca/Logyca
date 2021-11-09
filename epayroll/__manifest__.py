# -*- coding: utf-8 -*-

{
    'name': 'Epayroll',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'hr',
        'hr_payroll',
        'logyca',
        'hr_contract_types',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/type_epayroll_view.xml',        
        'views/hr_sub_type_job_view.xml',
        'views/hr_type_ejob_view.xml',
        'views/payment_form_epayroll_view.xml',
        'views/payment_method_epayroll_view.xml',
        'views/type_note_epayroll_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_payroll_structure_type_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_contract_etype_view.xml',
        'views/hr_contract_type_view.xml',
        'views/connection_server_view.xml',
        'views/epayslip_bach_run_view.xml',
        'views/epayslip_bach_view.xml',
        'views/epayslip_line_view.xml',
        'views/hr_electronictag_structure_view.xml',
        'views/ecertificate_view.xml',
        'views/res_company_view.xml',
        'views/hr_salary_rule_view.xml',
        'wizard/hr_epayslips_by_employees_view.xml',
        'wizard/hr_epayslips_note_wizard_view.xml',
        'data/hr_sub_type_job_data.xml',
        'data/hr_type_ejob_data.xml',
        'data/payment_form_epayroll_data.xml',
        'data/payment_method_epayroll_data.xml',
        'data/type_epayroll_data.xml',
        'data/type_note_epayroll_data.xml',
        'data/hr_contract_etype_data.xml',
        'data/epayslip_bach_data.xml',
    ],
    'qweb': [
    ]
}
