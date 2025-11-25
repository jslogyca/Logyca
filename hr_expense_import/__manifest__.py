# -*- coding: utf-8 -*-
{
    'name': 'HR Expense Import',
    'version': '17.0.1.0.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Import expense reports from Excel files',
    'description': """
        Import HR Expense Reports from Excel
        =====================================
        This module allows you to import expense reports (hr.expense.sheet) with their 
        corresponding expenses (hr.expense) from Excel files.
        
        Features:
        * Bulk import of expenses grouped by report
        * Validation of data before import
        * Support for budget groups and analytic accounts
        * Automatic partner product matching
        * Payment mode and credit card assignment
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
        'wizard/hr_expense_import_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
