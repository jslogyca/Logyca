# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountSectorRed(models.Model):
    _name= 'account.sector.red'
    _inherit = ['mail.thread']

    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, track_visibility='always')
    sect_red_ids = fields.One2many('sector.red', 'sect_red', string='Homologación', track_visibility='always')



class SectorRed(models.Model):
    _name= 'sector.red'


    sector_id = fields.Many2one('logyca.sectors', string='Sector')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Red de Valor')
    sect_red = fields.Many2one('account.sector.red', string='Sector - Red')