# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductRVC(models.Model):
    _name = 'product.rvc'
    _description = 'Product RVC'
    _rec_name = 'name'

    name = fields.Char(string='Product')
    code = fields.Char(string='Code')
    benefit_type = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica'),
                                    ('tarjeta_digital', 'Tarjeta Digital'),
                                    ('crece_mype', 'CreceMype')], string="Beneficio")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    state = fields.Selection([('activo', 'Activo'), 
                            ('inactivo', 'Inactivo')], string="State", default='activo')
