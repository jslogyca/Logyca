# -*- coding: utf-8 -*-

{
    'name': 'Payroll Request Loan',
    'summary': 'Payroll Request Loan',
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
        'l10n_co_lg_loan',
    ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'views/hr_request_loan_view.xml'
    ],
    'qweb': [
    ]
}
