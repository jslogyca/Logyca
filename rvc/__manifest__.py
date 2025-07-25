# -*- coding: utf-8 -*-

{
    'name': 'RVC',
    'summary': 'RVC',
    'version': '1.1',
    'category': 'Accounting/Accounting',
    'website': 'https://logyca.com',
    'author': 'LOGYCA',
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'depends': [
        'base',
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
        'report/rvc_report.xml',
        'data/notify_reminder_code_benefit_template.xml',
        'data/notify_codes_benefit_template.xml',
        'data/notify_colabora_benefit_template.xml',
        'data/welcome_kit_codes_benefit_template.xml',
        'data/welcome_kit_colabora_benefit_template.xml',
        'data/welcome_kit_digital_card_benefit_template.xml',
        # 'data/logyca_contact_types_data.xml',
        'data/cron_send_welcome_kit.xml',
        'data/cron_mark_benefit_as_rejected.xml',
        'data/cron_benefit_expiration_reminder.xml',
        # 'data/rvc_digital_card_off_services_data.xml',
        'data/welcome_kit_code_benefit_seller_template.xml',
        # 'data/notify_crecemype_template.xml',
        'security/ir.model.access.csv',
        'wizard/rvc_import_file_wizard_view.xml',
        'wizard/rvc_import_file_sponsored_wizard_view.xml',
        'wizard/rvc_template_email_wizard_view.xml',
        'wizard/rvc_template_email_confirm_wizard_view.xml',
        'wizard/rvc_template_email_done_wizard_view.xml',
        'wizard/rvc_template_email_re_done_wizard_view.xml',
        'wizard/send_notification_beneficiary_view.xml',
        'wizard/rvc_template_assignate_credentials.xml',
        'wizard/delivering_colabora_massively_view.xml',
        'wizard/rvc_crecemype_done_wizard_view.xml',
        'wizard/rvc_import_file_benefit_wizard_view.xml',
        'views/rvc_beneficiary_view.xml',
        'views/rvc_sponsor_view.xml',
        'views/config_rvc_view.xml',
        'views/log_import_rvc_view.xml',
        'views/product_rvc_view.xml',
        'views/rvc_crecemype_themes_view.xml',
        'views/benefit_application_view.xml',
        'views/report_mercantile_offer.xml',
        'views/report_rvc_bienv_codes_template.xml',
        'views/report_rvc_bienv_colabora_template.xml',
        'views/accept_benefit_template.xml',
        'views/already_accepted_benefit_template.xml',
        'views/reject_benefit_template.xml',
        'views/rvc_digital_card_views.xml',
        'views/res_partner_view.xml',
    ],
    'qweb': [
    ]
}
