# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_asset_range(models.Model):
    _name = 'logyca.asset_range'
    _description = 'Rangos de activos'
    
    initial_value = fields.Float(string='Valor inicial', required=True)
    final_value = fields.Float(string='Valor final', required=True)
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo')
    assigned_codes = fields.Integer(string='Nro. Asignación de codigos')

    def name_get(self):
        return [(record.id, '%s' %
                 (record.name)) for record in self]
