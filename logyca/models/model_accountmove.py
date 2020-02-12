# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo ACCOUNT-MOVE-LINE/ MOVIMIENTO DETALEE-------------------------------#

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    #PAÍS 
    x_country_account_id = fields.Many2one('res.country', string='País', store=True)