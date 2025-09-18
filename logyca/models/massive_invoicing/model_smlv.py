# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla parametrica para registrar el salario mínimo decretado para cada año
class x_MassiveInvoicingSMLV(models.Model):
    _name = 'massive.invoicing.smlv'
    _description = 'Massive Invoicing - SMLV'

    year = fields.Integer(string='Año', required=True)
    smlv = fields.Float(string='Valor SMLV', required=True)
    asset_range_ids = fields.One2many('massive.invoicing.smlv.ractive', 'smlv_id', string='Número Salarios Minimos Aporte')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Año: {} | SMLV: {}".format(record.year, record.smlv)))
        return result

    def purge_same_year(self):
        """Borra todas las tarifas del mismo año que self.year (excluye la actual si existe)."""
        self.ensure_one()
        domain = [('year', '=', self.year)]
        dupes = self.env['massive.invoicing.tariff'].search(domain)
        if dupes:
            dupes.unlink()  # usa dupes.sudo().unlink() si tus usuarios no tienen permisos de borrado
        product_ids = self.env['massive.invoicing.products'].search([('type_process', 'in', ('1','2','3','4'))])
        if self.asset_range_ids:
            for asset_range in self.asset_range_ids:
                for product_id in product_ids:
                    massive_tariff = {
                        'year': self.year,
                        'asset_range': asset_range.asset_range_id.id,
                        'type_vinculation': product_id.type_vinculation.id,
                        'product_id': product_id.product_id.id,
                        'fee_value': asset_range.tariff,
                    }
                    massive_tariff_obj = self.env['massive.invoicing.tariff'].create(massive_tariff)
        return True

class x_MassiveInvoicingSMLVRActive(models.Model):
    _name = 'massive.invoicing.smlv.ractive'
    _description = 'Massive Invoicing Rango Activos - SMLV'

    tariff = fields.Float(string="Número Salarios Mínimos Aporte",  digits=(16, 3), required=True, 
                default=0.0, copy=True, help="Se muestra con 3 decimales.")    
    asset_range_id = fields.Many2one('logyca.asset_range', string='Rango de Activos', required=True, copy=True)
    smlv_id = fields.Many2one('massive.invoicing.smlv', string='SMLV')
