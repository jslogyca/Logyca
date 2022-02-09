# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HRRequestLoanLine(models.Model):
    _name = 'hr.request.loan.line'
    _inherit = ['mail.thread']
    _description = "HR Request Loan Line"
    _order = "name desc"

    name = fields.Char('Name', tracking=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    input_id = fields.Many2one('hr.payslip.input.type', string='Input',tracking=True)
    request = fields.Selection([('new', 'New'), 
                                        ('shift', 'Shift')], string='Request')
    type_compute = fields.Selection([('fijo', 'Fijo'),
                                        ('amount', 'Amount'),
                                        ('fee', 'Fee')], string="Compute Type", track_visibility='onchange')
    date_from = fields.Date('Date From')
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    request_id = fields.Many2one('hr.request.loan', string="Request")
    date_request = fields.Date('Date Request')
    loan_id = fields.Many2one('hr.loan', string='Loan', tracking=True)

    def name_get(self):
        return [(line.id, '%s - %s' %
                 (line.employee_id.name, line.input_id.name)) for line in self]
