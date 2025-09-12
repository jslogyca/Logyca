{
    "name": "SARLAFT Tracking",
    "version": "18.0.1.0.0",
    "category": "Compliance",
    "summary": "SARLAFT queries registration and tracking system",
    "description": """
    SARLAFT Tracking Module
    =======================

    This module provides a structured and traceable system for recording SARLAFT
    (Sistema de Administración del Riesgo de Lavado de Activos y de la Financiación
    del Terrorismo) queries performed on customers, suppliers, and employees.

    Key Features:
    * Register and track SARLAFT queries
    * Mass import from Excel and CSV files
    * Automated notifications for upcoming queries
    * Integration with contacts and employees
    * Role-based access control
    """,
    "author": "Logyca",
    "website": "https://www.logyca.org",
    "depends": [
        "base",
        "contacts",
        "hr",
        "l10n_latam_base",
        "mail",
        "web",
    ],
    "data": [
        "security/sarlaft_security.xml",
        "security/ir.model.access.csv",
        "data/sarlaft_cron_data.xml",
        "data/system_parameters.xml",
        "views/sarlaft_tracking_views.xml",
        "views/res_partner_views.xml",
        "views/hr_employee_views.xml",
        "views/sarlaft_menus.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
    "license": "LGPL-3",
}
