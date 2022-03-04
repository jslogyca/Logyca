# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    
    partner_eps = fields.Many2one('res.partner', string='EPS', domain="[('type_reg_contribution', '=', 'eps')]")
    partner_fond_pens = fields.Many2one('res.partner', string='Fondo de Pensiones', domain="[('type_reg_contribution', '=', 'fond_pens')]")
    partner_fond_censa = fields.Many2one('res.partner', string='Fondo de Cesantías', domain="[('type_reg_contribution', 'in', ('fond_censa', 'fond_pens'))]")
    partner_arl = fields.Many2one('res.partner', string='ARL', domain="[('type_reg_contribution', '=', 'arl')]")
    partner_caja = fields.Many2one('res.partner', string='Caja de Compensación', domain="[('type_reg_contribution', '=', 'caja')]")



    