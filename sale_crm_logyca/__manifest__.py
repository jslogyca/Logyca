# -*- coding: utf-8 -*-

{
    'name': 'CRM - Sale - LOGYCA ',
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
        'sale',
        'product',
        'sales_team',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_view.xml',
        'views/crm_team_member_view.xml',
        'views/crm_team_view.xml',
        'wizard/crm_lead_import_file_wizard_view.xml',
    ],
    'qweb': [
    ]
}
