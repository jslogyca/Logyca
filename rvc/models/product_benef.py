# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class ProductBenef(models.Model):
    _name = 'product.benef'
    _description = 'Product Benef'

    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria')
    parent_id = fields.Many2one('rvc.sponsored', string='Empresa Patrocinadora')
    product_id = fields.Many2one('product.rvc', string='Producto')

#
