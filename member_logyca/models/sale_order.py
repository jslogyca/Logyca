# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    date_init_member_test = fields.Date(string='Inicio Periodo de Prueba Membresía', default=fields.Date.context_today)
    date_end_member_test = fields.Date(string='Final Periodo de Prueba Membresía', default=fields.Date.context_today)
    free_member = fields.Boolean(string='Periodo de Prueba', default=False)

