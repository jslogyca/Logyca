# -*- coding: utf-8 -*-
{
    "name": "HR Vacation XLSX Report",
    "version": "17.0.1.0",
    "author": "LORENA TORRES",
    "category": "Human Resources",
    "summary": "Reporte Excel de Vacaciones por Año/Mes",
    "depends": ["hr", "hr_holidays"],
    "data": [
        "security/ir.model.access.csv",
        "views/vacation_report_views.xml",
    ],
    "license": "OPL-1",
    "installable": True,
    "application": False,
}
