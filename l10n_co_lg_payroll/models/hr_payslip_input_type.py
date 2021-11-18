# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'

    type_input = fields.Selection([('loan', 'Loan'),
                              ('deduction', 'Deduction'),
                              ('overtime', 'Overtime'),
                              ('holidays', 'Holidays'),
                              ('no_aplica', 'No Aplica'), 
                              ('compensation_contract', 'Compensation Contract')], 'Input Type', select=True, required=True)
    active = fields.Boolean(default=True)
    percentage = fields.Float('Percentage')
    input_id = fields.Many2one("hr.salary.rule", string="Salary Rule Input")
    sequence = fields.Integer(required=True, index=True, default=10)

    def toggle_active(self):
        if self.active:
            self.active = False
        else:
            self.active = True