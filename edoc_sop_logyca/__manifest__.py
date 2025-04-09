# -*- coding: utf-8 -*-

{
    "name": "Doc. Soporte",
    "summary": "Doc. Soporte",
    "version": "1.1",
    'category': 'Accounting',
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
        "account",
        "epayroll",
    ],
    "description": """

========================

""",
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/type_operation_ds_data.xml",
        "data/form_send_ds_data.xml",
        "data/type_edocument_data.xml",
        "data/type_tributos_data.xml",
        "data/mode_payment_einvoice_data.xml",
        "data/form_payment_einvoice_data.xml",
        "views/res_company_view.xml",
        "views/account_journal_view.xml",
        "views/account_move_view.xml",
        "views/ir_sequence_dian_resolution_view.xml",
    ],
    "qweb": [],
}
