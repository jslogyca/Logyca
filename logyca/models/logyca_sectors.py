# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_sectors(models.Model):
    _name = 'logyca.sectors'
    _description = 'Sectores'

    code = fields.Char(string='Código', size=10,required=True)
    name = fields.Char(string='Nombre', required=True)
    macro_sector = fields.Selection([('manufactura', 'Manufactura'),
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.code)) for record in self]
