# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ConfigRVC(models.Model):
    _name = 'config.rvc'
    _description = 'RVC Config'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    product_id = fields.Many2one('product.product', string='Beneficio')
    type_beneficio = fields.Selection([('codigos', 'Identificación de Productos'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], string="Beneficio")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)