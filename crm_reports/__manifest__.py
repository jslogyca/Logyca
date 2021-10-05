# -*- coding: utf-8 -*-

{
    'name': 'Report CRM',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'account',
        'crm',
        'logyca',
        'base',
        'contacts',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'report/report_crm_contact_view.xml',
    ],
    'qweb': [
    ]
}
