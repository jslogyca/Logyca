{
    "name": "Survey QR Code",
    "version": "17.0.0.1",
    "summary": "Add QR codes to surveys for easy access and scanning.",
    "description": """This module enhances the Odoo Survey module by adding QR code generation capabilities for surveys.""",
    "category": "Tools",
    "author": "ITeSolution Team",
    "maintainer": "ITeSolution Software Services",
    "company": "ITeSolution Software Services",
    "website": "https://www.itesolution.co.in",
    "license": "LGPL-3",
    "depends": ["survey"],
    "data": [
        "security/ir.model.access.csv",
        # "wizards/survey_result_wizard_view.xml",
        "views/survey_views.xml",
        "views/assets.xml",
    ],
    "assets": {
        "survey.survey_assets": [
            "itesolution_survey_qrcode/static/src/css/survey_print.css",
        ],
    },
    "images": ["static/description/banner.png"],
    "installable": True,
    "auto_install": False,
    "application": True,
}
