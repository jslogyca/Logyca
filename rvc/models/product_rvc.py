# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ProductRVC(models.Model):
    _name = 'product.rvc'
    _description = 'Product RVC'
    _rec_name = 'name'

    name = fields.Char(string='Product')
    code = fields.Char(string='Code')
    type_beneficio = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], string="Beneficio")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    state = fields.Selection([('activo', 'Activo'), 
                            ('inactivo', 'Inactivo')], string="State", default='activo')
    sub_product_ids = fields.One2many('sub.product.rvc', 'product_id', string='Sub-Productos')
    



class SubProductRVC(models.Model):
    _name = 'sub.product.rvc'
    _description = 'Product RVC'
    _rec_name = 'name'


    name = fields.Char(string='Product')
    code = fields.Char(string='Code')
    state = fields.Selection([('activo', 'Activo'), 
                            ('inactivo', 'Inactivo')], string="State", default='activo')
    product_id = fields.Many2one('product.rvc', string='Product')
    cant_min = fields.Integer('Min.')
    cant_max = fields.Integer('Max.')
                            
