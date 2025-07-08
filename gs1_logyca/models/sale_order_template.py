# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    second_gs1 = fields.Boolean('Segundo Comunicado GS1', default=False)
