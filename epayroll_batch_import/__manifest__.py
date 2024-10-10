# -*- coding: utf-8 -*-

{
    'name': 'Epayroll Importar Archivo',
    'summary': 'Description',
    'version': '13.0.1.1.0',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'depends': [
        'hr_payroll'
        ],
    'description': '''

    ========================

    ''',    
    'data': [
        'wizard/import_file_wizard.xml',
        'views/hr_payroll_batch_import_menu.xml',
        'views/hr_salary_rule_view.xml'
    ],
    'qweb': []
}
