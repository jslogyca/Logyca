# -*- coding: utf-8 -*-

{
    "name": "LOGYCA Certification Report",
    "summary": "LOGYCA Certification Report",
    "version": "1.1",
    "category": "Accounting/Accounting",
    "website": "www.logyca.com",
    "author": "LOGYCA",
    'license': 'LGPL-3',
    "support": "lctorres@logyca.com",
    "maintainer": "LOGYCA",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "account",
    ],
    "description": """

========================

""",
    "data": [
        "data/config_certification_report_data.xml",
        "security/ir.model.access.csv",
        "wizard/account_certification_report_wizard_view.xml",
        "report/certification_report.xml",
        "views/reports.xml",
        "views/config_certification_report_view.xml",
        "views/menuitems.xml",
    ],
    "qweb": [],
}
