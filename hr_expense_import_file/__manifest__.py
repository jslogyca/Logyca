
# -*- coding: utf-8 -*-
{
    "name": "Expense Import File Wizard",
    "version": "17.0.1.0.0",
    "author": "LOGYCA / Lorena",
    "license": "LGPL-3",
    "category": "Human Resources/Expenses",
    "summary": "Importador de reportes de gastos y gastos desde Excel",
    "depends": [
        "hr_expense",
        "hr_expense_credit_card",
        "import_lead_crm_logyca",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_expense_import_file_wizard_view.xml",
    ],
    "application": False,
    "installable": True,
}
