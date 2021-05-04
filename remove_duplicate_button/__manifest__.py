# -*- coding: utf-8 -*-
{
    'name': "Remove Duplicate Button",

    'summary': """
        This module intends to hide the duplicate button in partner and product""",


    'author': "Juan Sebastián Ocampo for LOGYCA SERVICIOS S.A.S",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'extra tools',
    'version': '13.0.0.0.0',
    'installable': True,
	'application': True,
	'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': ['base'],
    
    # always loaded
    'data': [
        'views/res_partner_view.xml'
    ], 
    
}
