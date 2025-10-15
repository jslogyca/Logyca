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

    def purge_same_year_revenue(self):
        """Borra todas las tarifas del mismo año que self.year (excluye la actual si existe)."""
        self.ensure_one()
        domain = [('year', '=', self.year)]
        dupes = self.env['massive.income.tariff'].search(domain)
        if dupes:
            dupes.unlink()  # usa dupes.sudo().unlink() si tus usuarios no tienen permisos de borrado
        product_ids = self.env['massive.invoicing.products'].search([('type_process', 'in', ('1','2','3','4'))])
        if self.revenue_range_ids:
            for revenue_range in self.revenue_range_ids:
                for product_id in product_ids:
                    massive_tariff = {
                        'year': self.year,
                        'type_vinculation': product_id.type_vinculation.id,
                        'revenue_range': revenue_range.revenue_rang_id.id,
                        'product_id': product_id.product_id.id,
                        'old_value': revenue_range.old_value,
                        'fee_value': 0.0,
                        'unit_fee_value': revenue_range.tariff,
                    }
                    massive_tariff_obj = self.env['massive.income.tariff'].create(massive_tariff)
        return True


    def tariff_revenue_year(self):
        """Borra todas las tarifas del mismo año que self.year (excluye la actual si existe)."""
        self.ensure_one()
        domain = [('smlv_id', '=', self.year)]
        dupes = self.env['massive.invoicing.smlv.ig.active'].search(domain)
        if dupes:
            dupes.unlink()  # usa dupes.sudo().unlink() si tus usuarios no tienen permisos de borrado
        domain_now = [('year', '=', (self.year-1))]
        year = self.env['massive.invoicing.smlv'].search(domain_now)
        dupes_now = self.env['massive.invoicing.smlv.ig.active'].search([('smlv_id', '=', year.id)])        
        tariff = ((self.smlv*100)/year.smlv) - 100
        if dupes_now:
            for dupe_now in dupes_now:
                massive_tariff = {
                    'tariff': ((dupe_now.tariff*tariff)/100)+dupe_now.tariff,
                    'old_value': dupe_now.tariff,
                    'revenue_rang_id': dupe_now.revenue_rang_id.id,
                    'smlv_id': self.id,
                }
                massive_tariff_obj = self.env['massive.invoicing.smlv.ig.active'].create(massive_tariff)
        return True


class x_MassiveInvoicingSMLVRActive(models.Model):
    _name = 'massive.invoicing.smlv.ractive'
    _description = 'Massive Invoicing Rango Activos - SMLV'

    tariff = fields.Float(string="Número Salarios Mínimos Aporte",  digits=(16, 3), required=True, 
                default=0.0, copy=True, help="Se muestra con 3 decimales.")    
    asset_range_id = fields.Many2one('logyca.asset_range', string='Rango de Activos', required=True, copy=True)
    smlv_id = fields.Many2one('massive.invoicing.smlv', string='SMLV')

