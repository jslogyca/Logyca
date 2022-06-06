# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    salary_id = fields.Many2one('hr.salary.rule', string="Salary Rule", help="Salary Rule")
    leave_prima = fields.Boolean('Afecta Prima', default=False)
