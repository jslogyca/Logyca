# -*- coding: utf-8 -*-
{
    'name': 'Formulario Web de Ausencias',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Permite crear ausencias desde un formulario web público',
    'description': """
        Módulo que permite a los usuarios crear solicitudes de ausencia
        a través de un formulario web sin necesidad de autenticación.
    """,
    'author': 'Tu Empresa',
    'website': 'https://www.tuempresa.com',
    'depends': ['base', 'website', 'hr_holidays', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/website_leave_form_templates.xml',
        'views/hr_leave_type_views.xml',
        'data/mail_template.xml',
        'data/leave_summary_mail_template.xml',
        'data/leave_reminder_mail_template.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
