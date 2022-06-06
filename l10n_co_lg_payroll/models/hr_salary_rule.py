# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    constante_legal = fields.Boolean('Constant', default=False)
    rule_salary = fields.Boolean('Salary Rule', default=False)
    amount_fix = fields.Float(default=0.0, currency_field='company_currency_id', string='Fixed Amount', digits="Payroll Fix")
    base_prima = fields.Selection([('base_salary', 'Salary'),
                                ('variable_salary', 'Variable Salary')], string='Base Prima')
    aux_transp = fields.Boolean('Aux. Transp.', default=False)
    salary_const = fields.Boolean('Salary Const', default=False)
    base_cesantias = fields.Selection([('base_salary', 'Salary'),
                                ('variable_salary', 'Variable Salary')], string='Base Cesantías')

    @api.model
    def create(self, values):
        if not values.get('category_id', False):
            category_id = self.env.ref('l10n_co_mc_payroll.CONFIG').id
            values['category_id'] = category_id
        return super(HrSalaryRule, self).create(values)
