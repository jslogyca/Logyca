# -*- coding: utf-8 -*-
{
    'name': 'Survey Partner Validation',
    'version': '1.0',
    'category': 'Survey',
    'summary': 'Vincula encuestas con terceros por NIT y valida encuestas completadas antes de publicar facturas',
    'description': """
        Este módulo permite:
        - Asociar respuestas de encuesta con terceros (res.partner) mediante el NIT
        - Validar que terceros creados después del 31/10/2025 tengan encuesta completada
        - Bloquear publicación de facturas si no tienen encuesta completada
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['base', 'survey', 'account', 'partner_survey'],
    'data': [
        'security/ir.model.access.csv',
        'views/survey_user_input_views.xml',
        'views/res_partner_views.xml',
        'views/survey_survey_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
