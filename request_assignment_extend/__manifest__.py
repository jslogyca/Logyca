# -*- coding: utf-8 -*-

{
    "name": "Request Assignment LOGYCA Extend",
    "summary": "Request Assignment LOGYCA Extend",
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
        "request_assignment",
        "contacts"
    ],
    "description": """

========================
Request Assignment LOGYCA
""",
    "data": [
        "security/ir.model.access.csv",
        "views/request_partner_code_assignment_view.xml",
    ],
    "qweb": [],
}
