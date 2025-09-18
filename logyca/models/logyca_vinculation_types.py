# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_vinculation_types(models.Model):
    _name = 'logyca.vinculation_types'
    _description = 'Tipos de vinculación'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', size=100, required=True)
    active = fields.Boolean(string='Activo')
    novelty = fields.Selection([('1', 'Vigente'), ('2', 'No esta vigente para nuevos - se mantiene para las empresas que lo adquirieron')], string='Novedad', required=True)
    type_fm = fields.Boolean('Aplica FM', Default=False)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.code)) for record in self]
