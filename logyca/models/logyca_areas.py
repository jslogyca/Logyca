# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_areas(models.Model):
    _name = 'logyca.areas'
    _description = 'Áreas'
    _order = 'code,name'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.code)) for record in self]

