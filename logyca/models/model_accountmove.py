# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo ACCOUNT-MOVE / MOVIMIENTO-------------------------------#

class AccountMove(models.Model):
    _inherit = 'account.move'
    #PAÍS 
    x_country_account_id = fields.Many2one('res.country', string='País')