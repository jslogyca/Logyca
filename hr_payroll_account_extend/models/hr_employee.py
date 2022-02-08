# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    budget_group_id = fields.Many2one('logyca.budget_group', string='Budget Group')
