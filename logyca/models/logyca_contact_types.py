# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from random import randint


class x_contact_types(models.Model):
    _name = 'logyca.contact_types'
    _description = 'Tipos de contacto'
    
    def _get_default_color(self):
        return randint(1, 11)
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    color = fields.Integer(string='Color', default=_get_default_color)
    type_fe = fields.Boolean('Tipo FE', default=False)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.code)) for record in self]

