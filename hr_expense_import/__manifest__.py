# -*- coding: utf-8 -*-
{
    'name': 'HR Expense Import',
    'version': '17.0.2.0.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Import expense reports from Excel files with automatic detection and grouping options',
    'description': """
        Import HR Expense Reports from Excel
        =====================================
        This module allows you to import expense reports (hr.expense.sheet) with their 
        corresponding expenses (hr.expense) from Excel files.
        
        Features:
        * Bulk import of expenses grouped by report
        * Validation of data before import
        * Automatic detection of budget groups or analytic accounts (Column I)
        * Automatic partner product matching
        * Payment mode and credit card assignment
        * Optional CXP grouping when posting with credit cards
        
        Version 2.0.0 Changes:
        * Removed Column J (Analytic Account) - now integrated with Column I
        * Smart detection: Column I auto-detects budget groups or analytic accounts
        * New field: 'Agrupar por Factura' for grouped payables when posting
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'license': 'LGPL-3',
    'depends': [
        'hr_expense',
        'hr_expense_credit_card',
        'import_lead_crm_logyca',  # Para el modelo partner.product.purchase
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense_sheet_views.xml',
        # 'views/res_config_settings_views.xml',
        'wizard/hr_expense_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
