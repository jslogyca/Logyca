# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class FormPaymentEInvoice(models.Model):
    _name = 'form.payment.einvoice'
    _description = 'Form Payment EInvoice'
    
    # 13.3.4.1. Formas de Pago
    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', default=True)
    type = fields.Selection([('1', 'Contado'), 
                            ('2', 'Crédito')], string='Type', default='1')
    

    def name_get(self):
        return [(payment.id, '%s - %s' % (payment.code, payment.name)) for payment in self]
