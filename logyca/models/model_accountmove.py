# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo ACCOUNT-MOVE/ MOVIMIENTO DETALLE-------------------------------#

class AccountMove(models.Model):
    _inherit = 'account.move'
    #PAÍS 
    #x_country_account_id = fields.Many2one('res.country', string='País', store=True)
    x_country_account_id = fields.Many2one(comodel_name='res.country', related='partner_id.country_id', string='País', store=True)
    
# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#     #PAÍS 
#     x_country_account_id = fields.Many2one('res.country', string='País', store=True)