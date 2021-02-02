# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountAnalyticTag(models.Model):
    _inherit = 'account.analytic.tag'

    
    red_valor = fields.Boolean(string='Red de Valor')
    