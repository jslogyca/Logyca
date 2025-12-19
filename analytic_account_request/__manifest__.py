# -*- coding: utf-8 -*-
{
    'name': 'Solicitudes Web - Cuentas Analíticas, Tarjetas, Productos y Anticipos',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Permite solicitar la creación de cuentas analíticas, tarjetas de crédito, productos y anticipos mediante formularios web',
    'description': """
        Módulo que permite a los usuarios solicitar:
        1. Creación de cuentas analíticas
        2. Tarjetas de crédito corporativas
        3. Creación de productos
        4. Anticipos de dinero
        
        A través de formularios web públicos con flujo de aprobación completo.
        
        Características:
        - Formularios web públicos para solicitudes
        - Flujo de aprobación con estados
        - Notificaciones por email
        - Creación automática de cuentas analíticas
        - Gestión de aspectos legales para productos
        - Control de anticipos con política de legalización
        - Integración con hr.employee para obtener datos del solicitante
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['base', 'website', 'hr', 'mail', 'analytic', 'account'],
    'data': [
        'security/analytic_account_request_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/credit_card_mail_template.xml',
        'data/product_mail_template.xml',
        'data/advance_mail_templates.xml',
        'data/ir_sequence.xml',
        'views/analytic_account_request_views.xml',
        'views/analytic_account_request_templates.xml',
        'views/credit_card_request_views.xml',
        'views/credit_card_request_templates.xml',
        'views/product_request_views.xml',
        'views/product_request_templates.xml',
        'views/advance_request_views.xml',
        'views/advance_request_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
