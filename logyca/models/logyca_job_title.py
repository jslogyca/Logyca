# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_job_title(models.Model):
    _name = 'logyca.job_title'
    _description = 'Cargos'
    _order = 'area_id,code,name'

    area_id = fields.Many2one('logyca.areas', string='Área')
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.name, record.code)) for record in self]

