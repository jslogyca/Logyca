# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    
    red_valor = fields.Boolean(string='Red de Valor')
    