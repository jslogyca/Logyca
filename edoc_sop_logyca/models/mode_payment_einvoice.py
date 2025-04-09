# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ModePaymentEInvoice(models.Model):
    _name = 'mode.payment.einvoice'
    _description = 'Mode Payment EInvoice'
    
    # 13.3.4.2. Medios de Pago: cbc:PaymentMeansCode
    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)

    def name_get(self):
        return [(mode.id, '%s - %s' % (mode.code, mode.name)) for mode in self]
