# -*- coding: utf-8 -*-

{
    'name': 'Helpdesk LOGYCA',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'helpdesk',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/ir.model.access.csv',
        'data/helpdesk_station_data.xml',
        'data/helpdesk_service_data.xml',
        'data/helpdesk_ticket_subtype_data.xml',
        'views/helpdesk_team_view.xml',
        'views/helpdesk_station_view.xml',
        'views/helpdesk_ticket_view.xml',
        'views/helpdesk_service_view.xml',
        'views/helpdesk_ticket_subtype_view.xml',
    ],
    'qweb': [
    ]
}