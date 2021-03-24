# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    invoice_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta Red de Valor')
    inter_company = fields.Boolean('Intercompany', related='product_id.product_tmpl_id.inter_company', readonly=True, store=True)