# -*- coding: utf-8 -*-

{
    'name': 'RVC',
    'summary': 'Description',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': '',
    'application': False,
    'installable': True,
    'depends': [
        'account',
        'analytic',
        'logyca',
        'sale',
        ],
    'description': '''

========================

''',    
    'data': [
        'security/security.xml',
        'data/benefits_admon_data.xml',
        'data/aceptacion_beneficios_rvc_data.xml',
        'data/kitbienvenida_derechos_identificiacion.xml',
        'data/rechazo_beneficios_data.xml',
        'data/logyca_contact_types_data.xml',
        'security/ir.model.access.csv',
        'wizard/rvc_import_file_wizard_view.xml',
        'wizard/rvc_import_file_sponsored_wizard_view.xml',
        'wizard/rvc_template_email_wizard_view.xml',
        'wizard/rvc_template_email_confirm_wizard_view.xml',
        'wizard/rvc_template_email_done_wizard_view.xml',
        'wizard/rvc_template_email_rejected_wizard_view.xml',
        'views/rvc_beneficiary_view.xml',
        'views/rvc_sponsored_view.xml',
        'views/config_rvc_view.xml',
        'views/log_import_rvc_view.xml',
        'views/product_rvc_view.xml',
        'views/benefits_admon_view.xml',
        'report/rvc_report.xml',
        'views/report_rvc_templates.xml',
        'views/report_rvc_bienv_templates.xml',
        'views/accept_benefit_template.xml'
    ],
    'qweb': [
    ]
}
