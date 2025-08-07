# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'

    free_member = fields.Boolean(string='Periodo de Prueba', default=False)
    rango_type = fields.Selection([
        ('comercio', 'COMERCIO - DE $1 A $2.229.451.431'),
        ('manu', 'MANUFACTURA - DE $1 A $1.173.413.837'),
        ('service', 'SERVICIO - DE $1 A  $1.642.769.412'),
        ('other', 'MAYOR A  $2.229.451.431'),
    ], string="Rango de Ingresos", default='other')
