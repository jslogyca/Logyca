# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountSectorMacro(models.Model):
    _name= 'account.sector.macro'
    _description = 'Account Sector Macro'
    _inherit = ['mail.thread']

    
    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    sector_id = fields.Many2one('logyca.sectors', string='Sector')