{
    "name": "Odoo13 CRM Kit",
    'description': """Complete CRM Kit for odoo13, CRM, CRM dashboard, crm commission, commission plan, crm features""",
    'summary': """Complete CRM Kit for odoo13""",
    "category": 'Sales',
    "version": '17.0.1.0.0',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    "depends": ['base', 'sale_management', 'crm', 'crm_dashboard'],
    "data": [
        'security/ir.model.access.csv',
        'views/commission.xml',
        'wizard/commission_report.xml',
        'views/action_manager.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
