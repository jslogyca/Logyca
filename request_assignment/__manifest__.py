# -*- coding: utf-8 -*-

{
    "name": "Request Assignment LOGYCA",
    "summary": "Request Assignment LOGYCA",
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
    ],
    "description": """

========================
Request Assignment LOGYCA
""",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/request_partner_assignment_type_data.xml",
        "views/request_partner_assignment_type_view.xml",
        "views/request_partner_code_assignment_view.xml",
        "views/res_partner_view.xml",
    ],
    "qweb": [],
}
