# -*- coding: utf-8 -*-
{
    'name': 'Formulario Web de Ausencias',
    'version': '17.0.1.3.1',
    'category': 'Human Resources',
    'summary': 'Permite crear ausencias desde un formulario web público',
    'description': """
        Módulo que permite a los usuarios crear solicitudes de ausencia
        a través de un formulario web sin necesidad de autenticación.
        
        Versión 1.3.1:
        - Agregada validación de duración máxima de 1 día para tipos con restricción de semestre
        
        Versión 1.3.0:
        - Agregada imagen guía para incapacidades médicas en el formulario
        - Agregada validación de un día por semestre para tipos de ausencia específicos
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': ['base', 'website', 'hr_holidays', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_leave_form_views.xml',
        'views/website_leave_form_templates.xml',
        'views/hr_leave_type_views.xml',
        'data/mail_template.xml',
        'data/leave_summary_mail_template.xml',
        'data/leave_reminder_mail_template.xml',
        'data/ir_cron.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'website_leave_form/static/src/img/guia_incapacidades.png',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
