# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_responsibilities_rut(models.Model):
    _name = 'logyca.responsibilities_rut'
    _description = 'Responsabilidades RUT'

    code = fields.Char(string='Identificador', size=10, required=True)
    description = fields.Char(string='Descripción', size=100, required=True)
    valid_for_fe = fields.Boolean(string='Valido para facturación electrónica')
    display_name = fields.Char(
        string="Nombre completo",
        compute='_compute_display_name',
        store=True)

    @api.depends('code', 'description')
    def _compute_display_name(self):
        for rec in self:
            # concatena code y description, evitando 'None'
            rec.display_name = f"{rec.code or ''} - {rec.description or ''}"
