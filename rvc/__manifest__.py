# -*- coding: utf-8 -*-

{
    'name': 'RVC',
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
        'analytic',
        'logyca',
        'sale',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/rvc_import_file_wizard_view.xml',
        'wizard/rvc_import_file_sponsored_wizard_view.xml',
        'views/rvc_beneficiary_view.xml',
        'views/rvc_sponsored_view.xml',
        'views/config_rvc_view.xml',
        'views/log_import_rvc_view.xml',
    ],
    'qweb': [
    ]
}
