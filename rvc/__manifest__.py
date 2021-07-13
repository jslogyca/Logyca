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
        'data/product_benef_data.xml',
        'security/ir.model.access.csv',
        'wizard/rvc_import_file_wizard_view.xml',
        'wizard/rvc_import_file_sponsored_wizard_view.xml',
        'wizard/rvc_template_email_wizard_view.xml',
        'views/rvc_beneficiary_view.xml',
        'views/rvc_sponsored_view.xml',
        'views/config_rvc_view.xml',
        'views/log_import_rvc_view.xml',
        'views/product_rvc_view.xml',
        'views/sector_view.xml',
        'views/product_benef_view.xml',
        'views/agreement_rvc_view.xml',
    ],
    'qweb': [
    ]
}
