# -*- coding: utf-8 -*-

{
    'name': 'Import Leads CRM - LOGYCA ',
    'summary': 'Importación masiva de Leads y Órdenes de Compra con validaciones',
    'version': '1.4',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'crm',
        'sales_team',
        'purchase',
        'analytic',
        ],
    'description': '''
Módulo de Importación Masiva - LOGYCA
======================================

Funcionalidades:
- Importación masiva de Leads/Oportunidades CRM
- Importación masiva de Órdenes de Compra
- Validación de datos antes de importar
- Mapeo de productos por proveedor

Versión 1.3:
- Fix crítico: Corregido campo product_qty requerido
- Agregado campo product_uom para unidad de medida

Versión 1.2:
- Agregada columna "Descripción" para líneas de orden de compra
- Botón de validación de datos antes de importar
- Validación de grupos presupuestales
- Validación de cuentas analíticas
- Validación de proveedores
- Validación de referencias duplicadas
''',    
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/crm_lead_import_file_wizard_view.xml',
        'wizard/sale_order_import_file_wizard_view.xml',
        'views/partner_product_purchase_view.xml',
    ],
    'qweb': [
    ]
}
