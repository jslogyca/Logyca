# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HRPayrollAccountLine(models.Model):
    _name = 'hr.payroll.account.line'
    _inherit = ['mail.thread']
    _description = "Payroll Account Line"
    _order = "config_id desc"

    account_id = fields.Many2one('account.account', string='Journal')
    partner_id = fields.Many2one('res.partner', string='Partner')
    rule_ids = fields.Many2many('hr.salary.rule', string='Rules')
    nature = fields.Selection([('credit', 'Credit'),
                                ('debit', 'Debit')], string='Nature')
    by_partner = fields.Boolean('By Partner', default=False)
    by_entity = fields.Boolean('By Entity', default=False)
    by_cc = fields.Boolean('By CC', default=False)
    config_id = fields.Many2one('hr.payroll.account.config', string='Config')
    config_ss_id = fields.Many2one('hr.payroll.account.config', string='Config SS')
    config_prov_id = fields.Many2one('hr.payroll.account.config', string='Config Prov')
    item_id = fields.Many2one('hr.payroll.account.ss', string='Item')
    amount = fields.Float('Amount', default=0.0)
