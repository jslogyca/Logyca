# -*- coding: utf-8 -*-
{
    'name': 'Logyca Outgoing Mail Server Selector',
    'version': '17.0.1.0',
    'category': 'Mail',
    'summary': 'Automatic outgoing mail server selection based on document type and domain',
    'description': """
        This module automatically selects the appropriate outgoing mail server based on:
        - Document type (helpdesk.ticket, benefit.application, or others)
        - Domain extracted from reply_to field
        - Predefined business rules
    """,
    'author': 'Logyca',
    'depends': ['mail', 'base'],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
