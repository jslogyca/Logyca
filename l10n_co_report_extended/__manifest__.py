# -*- coding: utf-8 -*-
{
    'name': "Colombian Reports Extended",

    'summary': """
        This module intends to add/modify the localization reports""",


    'author': "Juan Sebastián Ocampo for LOGYCA SERVICIOS S.A.S",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting & Finance',
    'version': '13.0.0.0.1',
    'installable': True,
	'application': False,
	'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': ['l10n_co_reports'],
    
    # always loaded
    'data': [
        'data/l10n_co_reports.xml',
    ], 
    
}
