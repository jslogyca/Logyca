# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla parametrica para registrar el salario mínimo decretado para cada año
class x_MassiveInvoicingSMLV(models.Model):
    _name = 'massive.invoicing.smlv'
    _description = 'Massive Invoicing - SMLV'

    year = fields.Integer(string='Año', required=True)
    smlv = fields.Float(string='Valor SMLV', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Año: {} | SMLV: {}".format(record.year, record.smlv)))
        return result
