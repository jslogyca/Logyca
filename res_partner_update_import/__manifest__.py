# -*- coding: utf-8 -*-

{
    'name': 'Partner Update Import',
    'summary': 'Description',
    'version': '17.0.1.1.0',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'depends': [
        'base',
        'account',
        'contacts',
        ],
    'description': '''

    ========================

    ''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/res_partner_update_import_wizard.xml',
    ],
    'qweb': []
}
