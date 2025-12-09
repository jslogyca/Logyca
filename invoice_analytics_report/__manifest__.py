# -*- coding: utf-8 -*-
{
    'name': 'Invoice Analytics Report',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Reporte analítico de facturas con información detallada',
    'description': """
        Módulo de reporte analítico de facturas que incluye:
        - Vista PostgreSQL optimizada
        - Información de cliente y vinculación
        - Análisis por equipo y vendedor
        - Clasificación por sector y tamaño de empresa
        - Vistas tree y pivot para análisis
    """,
    'author': 'LOGYCA',
    'website': 'https://logyca.com',
    'depends': [
        'base',
        'account',
        'product',
        'crm',
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/invoice_analytics_report_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
