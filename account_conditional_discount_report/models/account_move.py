# -*- coding: utf-8 -*-

from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_conditional_discount_credit_note = fields.Boolean(
        string='NC por Descuento Condicionado',
        default=False,
        copy=False,
        readonly=True,
        help='Indica si esta nota crédito fue generada por el proceso automático de descuentos condicionados'
    )
