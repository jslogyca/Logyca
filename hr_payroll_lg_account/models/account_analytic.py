# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    type_id = fields.Many2one("account.analytic.type", string="Analytic Type")
