# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    invoice_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta Red de Valor')

class AccountMove(models.Model):
    _inherit = 'account.move'


    analytic_account_id = fields.Many2one('account.analytic.account', string='Red de Valor')