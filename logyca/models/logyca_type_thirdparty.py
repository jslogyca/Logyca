# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_type_thirdparty(models.Model):
    _name = 'logyca.type_thirdparty'
    _description = 'Tipos de tercero'
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    types = fields.Selection([('1', 'Cliente / Cuenta'),
                              ('2', 'Contacto'),
                              ('3', 'Proveedor'),
                              ('4', 'Funcionario / Contratista')], string='Tipo', required=True)

    def name_get(self):
        return [(record.id, '%s' %
                 (record.name)) for record in self]
