# -*- coding: utf-8 -*-
{
    'name': 'CRM NIT Extension',
    'version': '17.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Agrega campo NIT al módulo CRM',
    'description': """
        Módulo de extensión para CRM que agrega:
        - Campo NIT para las empresas en leads y oportunidades
        - Campo visible solo en leads (type='lead' o type=False)
    """,
    'author': 'LOGYCA',
    'website': 'https://www.logyca.com',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
