# -*- coding: utf-8 -*-

{
    'name': 'Import Leads CRM - LOGYCA ',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'crm',
        'sales_team',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_lead_import_file_wizard_view.xml',
    ],
    'qweb': [
    ]
}
