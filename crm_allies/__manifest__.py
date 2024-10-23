# -*- coding: utf-8 -*-

{
    "name": "CRM Allies - Benefits Membership",
    "summary": "CRM Allies - Benefits Membership",
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
        "logyca",
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
        "views/project_allies_view.xml",
        "views/reason_cancel_project_view.xml",
        "wizard/project_allies_cancel_wizard_view.xml",
        "wizard/benefi_import_file_member_wizard_view.xml",
    ],
    "qweb": [],
}
