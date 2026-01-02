# -*- coding: utf-8 -*-
{
    'name': 'Calculadora de Descuentos Condicionados en Ventas',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Cálculo automático de descuentos condicionados en órdenes de venta',
    'description': """
        Este módulo permite calcular descuentos condicionados en órdenes de venta
        según parámetros configurables de porcentajes de aumento y descuento
        con dos fechas diferentes.
        
        Características principales:
        - Búsqueda de órdenes por campo x_origen y rango de fechas
        - Cálculo automático de descuentos condicionados para dos fechas
        - Actualización de campos en sale.order y account.move
        - Selección múltiple de órdenes para procesamiento
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'account',
        'logyca',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/sale_conditional_discount_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
