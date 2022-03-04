# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class LogycaBudgetGroup(models.Model):
    _inherit = 'logyca.budget_group'

    type_id = fields.Many2one("account.analytic.type", string="Analytic Type")
