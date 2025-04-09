# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class EResponseBugs(models.Model):
    _name = 'eresponse.bugs'
    _order = 'id desc'
    _description = 'EResponse Bugs'

    send_ds_id = fields.Many2one('account.move', string='DS', readonly=True)
    code = fields.Char(string='Code')
    type = fields.Selection([
        ('sent', 'Send'),
        ('response', 'Response'),
        ('draft', 'Draft')
    ], required=True, default='draft')
    description = fields.Char(string='Description', required=True, readonly=True)

