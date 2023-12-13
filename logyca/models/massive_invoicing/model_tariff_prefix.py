# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla paramétrica para relacionar campos de la liquidación de la facturación - Tarifario
class MassiveTariffPrefix(models.Model):
    _name = 'massive.tariff.prefix'
    _description = 'Massive Tariff Prefix'
    
    _sql_constraints = [('tariff_prefix_unique', 'unique(year,type_vinculation,type_prefix,product_id)', 'Ya existe un tarifario con esta información, por favor verificar.')]
    
    #company_id = fields.Many2one('res.company', string='Compañia')
    year = fields.Integer(string='Año', required=True)
    type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación', track_visibility='onchange', ondelete='restrict', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    fee_value = fields.Float(string='Valor de la tarifa', required=True)
    type_prefix = fields.Selection([('6D', '6D'),
                                    ('5D', '5D'),
                                    ('4D', '4D'),
                                    ], string='Tipo de Prefix')
    size_prefix = fields.Selection([('999', '999'),
                                    ('9999', '9999'),
                                    ('99999', '99999'),
                                    ], string='Capacidad de Prefix')
    
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Año: {} | Tipo vinculación: {} | Rango de activos: {} | Producto: {}".format(record.year,record.type_vinculation.name, record.type_prefix,record.product_id.name)))
        return result
