# -*- coding: utf-8 -*-

{
    'name': 'RVC - Importación Masiva de Postulaciones',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Importación masiva de postulaciones desde Excel',
    'depends': ['base', 'rvc'],  # Ajustar 'rvc' al nombre de tu módulo
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizard_import_postulaciones_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}