# -*- coding: utf-8 -*-
{
    'name': 'HR Expense Credit Card',
    'version': '17.0.2.1.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Legalización de tarjetas de crédito corporativas',
    'description': """
        Módulo de personalización para legalización de gastos con tarjetas de crédito.
        
        Características principales:
        - Selección de proveedor en cada gasto individual
        - Nueva opción "Tarjeta de Crédito" en el campo "Pagado por"
        - Selección de proveedor al que va la factura en reportes de gastos
        - Generación automática de asientos contables con cuentas por pagar
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['hr_expense', 'account', 'logyca'],
    'data': [
        'security/ir.model.access.csv',
        'views/credit_card_views.xml',
        'views/hr_expense_views.xml',
        'views/hr_expense_sheet_views.xml',
    ],
    'demo': [
        'data/credit_card_demo.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
