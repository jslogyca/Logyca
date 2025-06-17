{
    "name": "No Auto Save",
    "version": "17.0.1.0.6",
    "summary": """
        Web module extention to give proper msg and do not auto save
    """,
    "sequence": 95,
    "author": "BizzAppDev Systems Pvt. Ltd.",
    "website": "http://www.bizzappdev.com",
    "category": "web",
    "depends": ["base", "web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "web_no_auto_save/static/src/js/web_no_auto_save.js",
            "web_no_auto_save/static/src/views/form/form_status_indicator/forms_status_indicator.scss",
        ],
    },
    "images": ["images/SaveChangesEE.png"],
    "license": "LGPL-3",
    "installable": True,
}
