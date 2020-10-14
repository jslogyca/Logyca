# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

# Modelo para guardar la información del pago, se llena por el api información enviada por Tienda Virtual
class PaymentInformation(models.Model):
    _name = 'logyca.payment.information'
    _description = 'Información de pago'
    
    partner_id = fields.Many2one('res.partner', string='Cliente', ondelete='restrict', required=True)
    move_name = fields.Char(string='N° Factura', required=True)
    move_id = fields.Many2one('account.move', string='Factura',readonly=True)
    amount_total = fields.Float(string='Valor recaudado',required = True)
    way_to_pay = fields.Char(string='Código forma de pago', required=True)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Información de pago - {}".format(record.move_id.name)))
        return result
    
    