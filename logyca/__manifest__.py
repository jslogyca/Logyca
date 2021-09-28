# -*- coding: utf-8 -*-
{
    'name': "logyca",

    'summary': """
        App LOGYCA""",

    'description': """
        App LOGYCA, creada con el fin de centralizar las personalizaciones realizadas a Odoo.
    """,

    'author': "Luis Buitrón & Santiago Torres",
    
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',
    'installable': True,
	'application': True,
	'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': ['base','account','contacts','crm','sale_management','helpdesk','purchase','survey','documents','account_asset','approvals','account_budget'],
    
    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/parameterization_views.xml',
        'views/ciiu_view.xml',
        'views/reports.xml',
        'views/menus.xml',     
        'views/logyca_survey.xml',
        'views/massive_invoicing_views.xml',
        'views/res_partner_views.xml',
        'views/account_journal_views.xml',
        'views/account_move_report_invoice.xml'
    ], 
    
}
