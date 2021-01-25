# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class LogycaBudgetGroup(models.Model):
    _inherit = 'logyca.budget_group'


    invoice_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta Red de Valor')