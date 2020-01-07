# -*- coding: utf-8 -*-
{
    'name': "logyca",

    'summary': """
        App LOGYCA""",

    'description': """
        App LOGYCA
    """,

    'author': "Luis Buitrón",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '1.0',
    'installable': True,
	'application': True,
	'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': ['base','account','contacts'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/parameterization_views.xml',
        'views/ciiu_view.xml',
        'views/menus.xml',     
    ],    
}