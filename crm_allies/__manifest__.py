# -*- coding: utf-8 -*-

{
    "name": "CRM Allies - Benefits Membership",
    "summary": "CRM Allies - Benefits Membership",
    "version": "1.1",
    'category': 'Sales/CRM',
    "website": "www.logyca.com",
    "author": "LOGYCA",
    "license": "",
    "support": "lctorres@logyca.com",
    "maintainer": "LOGYCA",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "contacts",
    ],
    "description": """

========================

""",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/benefits_membership_partner_view.xml",
        "views/benefits_membership_view.xml",
        "views/categ_benefits_membership_view.xml",
        # "views/res_partner_view.xml",
    ],
    "qweb": [],
}
