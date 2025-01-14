# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class ConfigCertificationReport(models.Model):
    _name = "config.certification.report"
    _description = "Config Certification Report"

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 default=lambda self: self.env.company)
    tax_ids = fields.Many2many('account.tax',
                               'report_conf_tax_default_rel',
                               'tax_id',
                               'report_conf_id',
                               string='Default Taxes',
                               check_company=True,
                               context={'append_type_to_tax_name': True})
    active = fields.Boolean(default=True,
                            help="Set active to false to hide the"
                                 "Config without removing it.")
    by_city = fields.Boolean('By City', default=False)
    city_id = fields.Many2one('res.city', string='City')
    note = fields.Text('Comment')
    account_ids = fields.Many2many('account.account',
                               'report_conf_account_default_rel',
                               'account_id',
                               'report_conf_id',
                               string='Default Account',
                               check_company=True)

