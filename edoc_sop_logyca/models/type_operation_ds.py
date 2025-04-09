# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class TypeOperationDS(models.Model):
    _name= 'type.operation.ds'
    _description = "Types of Operation DS"

    # 13.1.5 Tipos de Operación Documento Soporte
    name = fields.Text('Name', required=True)
    code = fields.Char('Code', required=True)

    def name_get(self):
        return [(type.id, '%s - %s' % (type.code, type.name)) for type in self]
