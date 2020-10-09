# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# Tabla parametrica para textileros que identifica los códigos por CESION
class x_MassiveInvoicingCodesAssignment(models.Model):
    _name = 'massive.invoicing.codes.assignment'
    _description = 'Massive Invoicing - Codes Assignment'
    
    prefix = fields.Char(string='Prefijo', required=True)    
    company_yields = fields.Many2one('res.partner', string='Empresa que cede', required=False)
    company_receives = fields.Many2one('res.partner', string='Empresa que recibe el código', required=True)
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Prefijo: {} | Empresa que recibe el código: {}".format(record.prefix, record.company_receives.name)))
        return result
