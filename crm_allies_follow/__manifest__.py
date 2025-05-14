# -*- coding: utf-8 -*-

{
    "name": "CRM Allies - Follow",
    "summary": "CRM Allies - Follow",
    "version": "1.1",
    'category': 'Sales/CRM',
    "website": "www.logyca.com",
    "author": "LOGYCA",
    'license': 'LGPL-3',
    "support": "lctorres@logyca.com",
    "maintainer": "LOGYCA",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "contacts",
        "crm_allies",
    ],
    "description": """

========================

""",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/follow_partner_loyalty_view.xml",
        "views/res_partner_view.xml",
    ],
    "qweb": [],
}
