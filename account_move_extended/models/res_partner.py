# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    income_ids = fields.One2many('revenue.macro.sector.partner', 'partner_id', string='Ingresos')
    size_sector_int = fields.Selection([('micro1', 'Micro 1'),
                                        ('micro2', 'Micro 2'),
                                        ('micro3', 'Micro 3'), 
                                        ('pequena1', 'Pequeña 1'),
                                        ('pequena2', 'Pequeña 2'),
                                        ('pequena3', 'Pequeña 3'),
                                        ('mediana1', 'Mediana 1'),
                                        ('mediana2', 'Mediana 2'),
                                        ('mediana3', 'Mediana 3'),
                                        ('grande1', 'Grande 1'),
                                        ('grande2', 'Grande 2'),
                                        ('grande3', 'Grande 3'),
                                        ('grande4', 'Grande 4'),
                                    ('grande5', 'Grande 5')], string='Tamaño Empresa Interno')
    fact_annual = fields.Selection([('activos', 'Por Activos'), 
                                    ('ingresos', 'Por Ingresos')], string='Facturación Anual', default='activos', track_visibility='onchange')
    amount_revenue_membre = fields.Float('Ingresos Memebresía', default=0.0)
    revenue_memb_ids = fields.Many2one('revenue.macro.sector', string='Rango de Ingresos Membresía')


    def action_update_revenue_partner(self):
        view_id = self.env.ref('account_move_extended.update_revenue_wizard_wizard_view').id,
        return {
            'name':_("Actualizar Ingresos"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'update.revenue.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }


    def action_update_revenue_partner_membre(self):
        view_id = self.env.ref('account_move_extended.update_revenue_wizard_wizard_view_mb').id,
        return {
            'name':_("Actualizar Ingresos Membresía"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'update.revenue.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }    