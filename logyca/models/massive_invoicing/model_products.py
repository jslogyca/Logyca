# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla parametrica para registrar el manejo de los productos
class x_MassiveInvoicingProducts(models.Model):
    _name = 'massive.invoicing.products'
    _description = 'Massive Invoicing - Products'

    type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación', ondelete='restrict', required=True)
    type_process = fields.Selection([
                                        ('1', 'Renovación Vinculación'),
                                        ('2', 'Renovación Prefijos Adicionales'),                                        
                                        ('3', 'Renovación Prefijos GTIN8'),
                                        ('4', 'Renovación Prefijos'),
                                    ], string='Tipo de Proceso', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {} | {}".format(record.type_vinculation, record.type_process,record.product_id)))
        return result
