# -*- coding: utf-8 -*-

{
    'name': 'Account Mass Logyca',
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
        'logyca',
        'base',
        'account_move_extended',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        # 'data/config_discount_logycaedx_data.xml',
        'views/config_discount_logycaedx_view.xml',
        'views/config_discount_log_revenue_view.xml',
        'views/partner_logycaedx_view.xml',
        'views/partner_logyca_revenue_view.xml',
    ],
    'qweb': [
    ]
}
