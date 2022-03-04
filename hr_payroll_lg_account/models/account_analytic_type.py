# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class AccountAnalyticType(models.Model):
    _name = 'account.analytic.type'
    _rec_name = 'name'
    _description = 'Account Analytic Type'

    name = fields.Char('Name')
    code = fields.Char('code')
    active = fields.Boolean('Active', default=True)
