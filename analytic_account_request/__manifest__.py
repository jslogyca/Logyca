# -*- coding: utf-8 -*-
{
    'name': 'Solicitud de Cuentas Analíticas, Tarjetas de Crédito y Productos',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Permite solicitar la creación de cuentas analíticas, tarjetas de crédito y productos mediante formularios web',
    'description': """
        Módulo que permite a los usuarios solicitar:
        1. Creación de cuentas analíticas
        2. Tarjetas de crédito corporativas
        3. Creación de productos
        
        A través de formularios web públicos con flujo de aprobación completo.
        
        Características:
        - Formularios web públicos para solicitudes
        - Flujo de aprobación con estados
        - Notificaciones por email
        - Creación automática de cuentas analíticas
        - Gestión de aspectos legales para productos
        - Integración con hr.employee para obtener datos del solicitante
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['base', 'website', 'hr', 'mail', 'analytic'],
    'data': [
        'security/analytic_account_request_security.xml',
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/credit_card_mail_template.xml',
        'data/product_mail_template.xml',
        'data/ir_sequence.xml',
        'views/analytic_account_request_views.xml',
        'views/analytic_account_request_templates.xml',
        'views/credit_card_request_views.xml',
        'views/credit_card_request_templates.xml',
        'views/product_request_views.xml',
        'views/product_request_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
