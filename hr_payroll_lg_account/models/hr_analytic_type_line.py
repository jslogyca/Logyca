# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HRAnalyticTypeLine(models.Model):
    _name = 'hr.analytic.type.line'
    _description = "HR Analytic Type Line"
    _order = "analytic_type_id asc"

    company_id = fields.Many2one( "res.company", string="Company", default=lambda self: self.env.company)
    analytic_type_id = fields.Many2one('account.analytic.type', string='Type')
    account_id = fields.Many2one('account.account', string='Account')
    type_account = fields.Selection([('debit', 'Cuenta Deudora'),
                                ('credit', 'Cuenta Acreedora')], string='Type Account')
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
