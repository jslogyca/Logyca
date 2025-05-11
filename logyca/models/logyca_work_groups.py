# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_work_groups(models.Model):
    _name = 'logyca.work_groups'
    _description = 'Grupos de Trabajo'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.name)) for record in self]
