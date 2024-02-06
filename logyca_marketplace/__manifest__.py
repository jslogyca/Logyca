# -*- coding: utf-8 -*-

{
    'name': 'LOGYCA Marketplace',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': True,
    'installable': True,
    'depends': [
        'base',
        'account',
        'rvc',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_marketplace_view.xml',
        'views/rel_res_partner_marketplace_view.xml',
        'views/res_partner_view.xml',
    ],
    'qweb': [
    ]
}
