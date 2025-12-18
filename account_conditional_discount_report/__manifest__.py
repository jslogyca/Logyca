{
    'name': 'Reporte de Descuentos Comerciales Condicionados',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte en Excel de descuentos condicionados para generación de notas crédito',
    'description': """
        Módulo para identificar descuentos comerciales condicionados registrados en la cuenta 530535
        y generar un reporte en Excel con la información necesaria para crear notas crédito.
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/conditional_discount_report_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
