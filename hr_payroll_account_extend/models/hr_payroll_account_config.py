# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HRPayrollAccountConfig(models.Model):
    _name = 'hr.payroll.account.config'
    _inherit = ['mail.thread']
    _description = "Payroll Account Config"
    _order = "id desc"

    ref = fields.Char('Referencia', tracking=True)
    description = fields.Char('Description', tracking=True)
    date = fields.Date('Date')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    journal_ss_id = fields.Many2one('account.journal', string='Journal SS')
    journal_prov_id = fields.Many2one('account.journal', string='Journal Prov')
    line_ids = fields.One2many('hr.payroll.account.line', 'config_id', string='Lines')
    account_id = fields.Many2one('account.account', string='Account')
    line_ss_ids = fields.One2many('hr.payroll.account.line', 'config_ss_id', string='Lines SS')
    line_prov_ids = fields.One2many('hr.payroll.account.line', 'config_prov_id', string='Lines Prov')

    def name_get(self):
        return [(config.id, '%s - %s' % (config.ref, config.journal_id)) for config in self]
