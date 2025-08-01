# -*- coding: utf-8 -*-
{
    'name': 'Logyca - Base Optional Quick Create Frontend Only',
    'version': '17.0.1.0.0',
    'category': 'Logyca/Technical',
    'summary': 'Logyca customization: Restrict quick create only in frontend, allow backend operations',
    'description': """
        Logyca Customization
        ====================
        
        This module extends base_optional_quick_create to only block quick creation
        from the frontend (user interface) while allowing backend operations like
        those from Helpdesk, Mail, Portal, etc.
        
        Key features:
        - Blocks quick creation only from frontend RPC calls
        - Allows programmatic creation from backend modules
        - Maintains all original functionality
        - Compatible with Helpdesk automatic contact creation
        
        Developed specifically for Logyca requirements.
    """,
    'author': 'Logyca',
    'website': 'https://www.logyca.org',
    'license': 'AGPL-3',
    'depends': [
        'base_optional_quick_create',
    ],
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
