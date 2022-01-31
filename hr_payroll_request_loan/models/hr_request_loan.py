# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HRRequestLoan(models.Model):
    _name = 'hr.request.loan'
    _inherit = ['mail.thread']
    _description = "HR Request Loan"
    _order = "name desc"

    name = fields.Char('Name', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, tracking=True)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    lines_ids = fields.One2many('hr.request.loan.line', 'request_id', string="Request Line", index=True)
    state = fields.Selection([('draft', 'Draft'),
                                    ('open', 'Open'),], string='Status', default='draft')

    def action_open(self):
        self.write({'state': 'open'})

    def action_draft(self):
        self.write({'state': 'draft'})
