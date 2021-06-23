# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class TypeEPayroll(models.Model):
    _name = 'type.epayroll'
    _description = 'Type EPayroll'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    type = fields.Selection([('epayroll', 'Documento Soporte de Pago de Nómina Electrónica'), 
                            ('epayroll_ajus', 'Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica')], string='Tipo de XML')
    

#