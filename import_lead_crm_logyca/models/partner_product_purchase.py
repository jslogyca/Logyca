# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class PartnerProductPurchase(models.Model):
    _name = 'partner.product.purchase'
    _description = 'Partner Product Purchase'

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Partner')
    product_id = fields.Many2one('product.product', string='Product')
    product_type = fields.Selection([
        ('ga', 'Gasto'),
        ('gv', 'Venta'),
        ('co', 'Costo'),
        ('na', 'N/A')], string="Tipo")
    amount_type = fields.Selection([
        ('total', 'Total'),
        ('consumo', 'Consumo'),
        ('corretaje', 'Corretaje'),
        ('na', 'N/A')], string="Tipo Total")
