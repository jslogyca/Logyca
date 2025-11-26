# -*- coding: utf-8 -*-

{
    'name': 'MEMBERS - LOGYCA ',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'logyca',
        'contacts',
        'sale',
        'website_sale',
        'l10n_latam_base',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/sale_order_template.xml',
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'views/checkout_templates_view.xml',
        'views/sale_order_loyalty_template.xml',
        'wizard/member_tyb_wizard_view.xml',
    ],
    'qweb': [
    ]
}
