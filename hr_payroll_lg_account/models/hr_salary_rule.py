# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    analytic_type_ids = fields.One2many('hr.analytic.type.line', 'salary_rule_id', string="Account Analytic Type")
    register_id = fields.Many2one(
        "hr.contribution.register",
        string="Contribution Register",
        help="Eventual third party involved in the salary payment of the employees.",
    )
    register_credit_id = fields.Many2one(
        "hr.contribution.register",
        string="Contribution Register Credit",
        help="Eventual third party involved in the salary payment of the employees.",
    )
