# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # obligation_ids = fields.One2many('type.obligation.partner', 'partner_id', string='Fiscal responsibility')
    # einvice_payment_id = fields.Many2one('mode.payment.einvoice', string='mode payment einvoice')
    # type_operation = fields.Many2one('type.operation', string='Operation Type')
    type_operation_ds = fields.Many2one('type.operation.ds', string='Operation Type DS')
