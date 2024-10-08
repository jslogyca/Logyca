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
    'depends': [
        'base',
        'account',
        'contacts',
        'crm',
        'sale_management',
        'helpdesk',
        'purchase',
        'survey',
        'documents',
        'account_asset',
        'approvals',
        'l10n_latam_base',
        'purchase_order_type',
        'account_budget'
    ],
    
    # always loaded 
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_get_invoice_dian_status.xml',
        'views/res_partner_views.xml',
        'views/collaborative_group_views.xml',
        'views/parameterization_views.xml',
        'views/ciiu_view.xml',
        'views/reports.xml',
        'views/massive_invoicing_views.xml',
        'views/menus.xml',
        'views/logyca_survey.xml',
        'views/account_journal_views.xml',
        'views/account_move_report_invoice.xml',
        'views/model_tariff_prefix_view.xml',
        'report/account_debtors_report_view.xml',
        'views/massive_invoicing_companies_view.xml',
        'views/massive_invoicing_smlv_view.xml',
        'views/massive_invoicing_codes_assignment_view.xml',
        'views/massive_invoicing_tariff_view.xml',
        'views/massive_invoicing_tariff_discounts_view.xml',
        'views/massive_invoicing_products_view.xml',
        'views/logyca_budget_group_view.xml',
        'views/logyca_type_thirdparty_view.xml',
        'views/account_move_view.xml',
        'views/logyca_reports_account_view.xml',
        'views/account_asset_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        'views/product_template_view.xml',
    ], 
    
}
