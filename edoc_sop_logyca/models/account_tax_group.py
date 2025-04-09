# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    code = fields.Char(translate=True, string='Tax Code registered in the Electronic Invoice') 
    tributo_id = fields.Many2one('type.tributos', string='Tributo')

    
    @api.onchange('tributo_id')
    def _onchange_tributo_id(self):
        if self.tributo_id:
            self.code = self.tributo_id.code
    
    