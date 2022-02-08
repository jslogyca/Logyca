# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HRPayrollAccountSS(models.Model):
    _name = 'hr.payroll.account.ss'
    _inherit = ['mail.thread']
    _description = "Payroll Account SS"
    _order = "id desc"

    description = fields.Char('Description', tracking=True)
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, tracking=True)
    item_ids = fields.One2many('hr.payroll.account.ss.line', 'item_id', string='Lines')
    type_afp = fields.Selection([('eps', 'EPS'),
                                ('afp', 'AFP')], string='Nature')    

    def name_get(self):
        return [(config.id, '%s - %s' % (config.description, config.date)) for config in self]

    @api.onchange('item_ids', 'item_ids.amount')
    def get_item_ids(self):
        if self.type_afp=='eps':
            for line in self.item_ids:
                line.amount_employee = ((line.amount)/0.125)*0.04
        else:
            for line in self.item_ids:
                line.amount_employee = ((line.amount)/0.16)*0.04

class HRPayrollAccountSSLine(models.Model):
    _name = 'hr.payroll.account.ss.line'
    _inherit = ['mail.thread']
    _description = "Payroll Account SS Line"
    _order = "item_id desc"

    partner_id = fields.Many2one('res.partner', string='Partner')
    code = fields.Char('Code', tracking=True)
    amount = fields.Float('Amount', default=0.0)
    amount_employee = fields.Float('Amount Employee', default=0.0)
    item_id = fields.Many2one('hr.payroll.account.ss', string='Config')

    @api.onchange('amount')
    def get_amount(self):
        if self.item_id.type_afp=='eps':
            self.amount_employee = ((self.amount)/0.125)*0.04
        else:
            self.amount_employee = ((self.amount)/0.16)*0.04
