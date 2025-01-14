# -*- coding: utf-8 -*-

import calendar
import datetime
import operator

from odoo import _, api, fields, models
from odoo.tools import float_is_zero


class AccountCertificationHeader(models.Model):
    _name = "account.certification.header"
    _description = "Account Certification Header"

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', string='Partner')
    date_from = fields.Date(string='Fecha Inicio')
    date_to = fields.Date(string='Fecha Fin')
    date = fields.Date(string='Fecha Expedición')
    report_line = fields.One2many('account.certification.header.line', 'header_id', 'Lines')
    date_expe = fields.Date('Date Expe')
    total_amount = fields.Float(string='Total')
    by_city = fields.Boolean('By City', default=False)
    default_rep_id = fields.Many2one('config.certification.report', string='Report Config')
    file_name = fields.Char("File name")
    currency_id = fields.Many2one('res.currency', string='Currency')
    note = fields.Text('Comment')
    base = fields.Float(string='Base')
    amount = fields.Float(string='Amount')

class AccountCertificationStructLine(models.Model):
    _name = "account.certification.header.line"
    _description = "Account Certification Header Line"

    header_id = fields.Many2one('account.certification.header', string='Header')
    note = fields.Char('Notes')
    account_id = fields.Many2one('account.account', string='Cuenta')
    tax_id = fields.Many2one('account.tax', string='Tax')
    partner_id = fields.Many2one('res.partner', string='Partner')
    city_id = fields.Many2one('res.city', string='City')
    base = fields.Float(string='Base')
    amount = fields.Float(string='Amount')
    tax_percent = fields.Float(string='Tarifa')
