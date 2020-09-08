# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)

#---------------------------Modelos Aprobaciones-------------------------------#

class ApprovalRequest(models.Model):
    _inherit = 'approval.request'          
    
    @api.model
    def _get_account_move(self):
        move = None
        if self.env.context.get('x_account_move_id', False):
            move = self.env['account.move'].browse(self.env.context.get('x_account_move_id'))
        return move
    
    @api.model
    def _get_category(self):
        category = None
        if self.env.context.get('category_id', False):
            category = self.env['account.move'].browse(self.env.context.get('category_id'))
        return category
    
    @api.model
    def _get_owner(self):
        owner = None
        if self.env.context.get('request_owner_id', False):
            owner = self.env['account.move'].browse(self.env.context.get('request_owner_id'))
        return owner
    
    #Movimiento contable
    x_account_move_id = fields.Many2one('account.move', string='Factura Asociada',readonly=True, default=_get_account_move)
    #Context Category
    category_id = fields.Many2one('approval.category', string="Category", required=True,default=_get_category)
    #Propietario
    request_owner_id = fields.Many2one('res.users', string="Request Owner",default=_get_owner)
    

class ApprovalRequest(models.Model):
    _inherit = 'approval.category'        
    
    x_approval_nc = fields.Boolean('¿Es aprobación para Nota Crédito?')
    