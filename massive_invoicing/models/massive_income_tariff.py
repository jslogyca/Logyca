# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla paramétrica para relacionar campos de la liquidación de la facturación - Tarifario
class x_MassiveInvoicingTariff(models.Model):
    _name = 'massive.income.tariff'
    _description = 'Massive Income - Tariff'
    
    _sql_constraints = [('tariff_presence_unique', 'unique(year,type_vinculation,revenue_range,product_id)', 'Ya existe un tarifario con esta información, por favor verificar.')]
    
    #company_id = fields.Many2one('res.company', string='Compañia')
    year = fields.Integer(string='Año', required=True)
    type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación', track_visibility='onchange', ondelete='restrict', required=True)
    revenue_range = fields.Many2one('revenue.macro.sector', string='Rango de Ingresos', track_visibility='onchange', ondelete='restrict', required=True)
    macro_sector = fields.Selection(related='revenue_range.macro_sector', string='Macrosector')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    old_value = fields.Float(string='Tarifa Anterior', required=True, default=0.0)
    fee_value = fields.Float(string='Valor de la tarifa', required=True)
    unit_fee_value = fields.Float(string='Tarifa unitaria', help='Cálculo de la tarifa UNITARIA redondeando a la milésima más cercana: ROUND(SMLV * Valor de la tarifa,-3).',compute='_compute_unit_fee_value', store=True, track_visibility='onchange')
    
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Año: {} | Tipo vinculación: {} | Rango de ingresos: {} | Producto: {}".format(record.year,record.type_vinculation.name, record.revenue_range.amount,record.product_id.name)))
        return result
    
    @api.depends('fee_value', 'old_value')
    def _compute_unit_fee_value(self):
        #date = fields.Date.today()
        #year = date.year
        year = self.year
        obj_smlv = self.env['massive.invoicing.smlv'].search([('year', '=', year)])
        smlv = 0
        for i in obj_smlv:
            smlv = obj_smlv.smlv        
        
        self.unit_fee_value = round((smlv*self.fee_value)+self.old_value,-3)


# Al tarifario adicionar los siguientes campos para que sean digitados o importados anualmente por el área encargada de facturación masiva
# Para realizar esto se crea una tabla secundaria con esta información
# class x_MassiveIncomeTariffDiscounts(models.Model):
#     _name = 'massive.income.tariff.discounts'
#     _description = 'Massive Income - Tariff Discounts'
    
#     _sql_constraints = [('tariff_discounts_presence_unique', 'unique(tariff)', 'Un tarifario solo puede estar asociado a un tarifario de descuento.')]
    
#     tariff = fields.Many2one('massive.income.tariff', string='Tarifario por Ingresos', ondelete='restrict', required=True)
#     discount_percentage = fields.Integer(string='Descuento antes de IVA (%)', required=True)
#     discounts_one = fields.Float(string='Valor descuento')
#     date_discounts_one = fields.Date(string='Fecha descuento', help='Fecha hasta la cual aplica el descuento 1')    
    #is_billed = fields.Boolean(string='¿Se factura?')