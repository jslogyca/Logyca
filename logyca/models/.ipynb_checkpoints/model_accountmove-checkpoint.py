# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests

#---------------------------Modelo ACCOUNT-MOVE/ MOVIMIENTO DETALLE-------------------------------#

# Encabezado Movimiento
class AccountMove(models.Model):
    _inherit = 'account.move'
    
      
    #PAÍS 
    x_country_account_id = fields.Many2one('res.country', string='País', track_visibility='onchange')
    #NUMERO DE ORDEN DE COMPRA
    x_num_order_purchase = fields.Char(string='Número orden de compra', track_visibility='onchange')
    #FACTURACIÓN ELECTRONICA
    x_date_send_dian = fields.Datetime(string='Fecha de envío a la DIAN')
    x_send_dian = fields.Boolean(string='Enviado a la DIAN')
    x_cufe_dian = fields.Char(string='CUFE - Código único de facturación electrónica')
    x_motive_error = fields.Text(string='Motivo de error')
    
    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _onchange_partner_id_country(self):
        
        partner = self.env['res.partner'].browse(self.partner_id.id)
        
        values = {
                'x_country_account_id': partner.country_id ,                
            }
        self.update(values)
    
    #Validaciones antes de permitir PUBLICAR una factura
    def action_post(self): 
        partner = self.env['res.partner'].browse(self.partner_id.id)
        cant_contactsFE = 0
        for record in partner.child_ids:   
            ls_contacts = record.x_contact_type              
            for i in ls_contacts:
                if i.id == 3:
                    cant_contactsFE = cant_contactsFE + 1
        
        if cant_contactsFE > 0:
            return super(AccountMove, self).action_post()
        else:
            raise ValidationError(_('El cliente al que pertenece la factura no tiene un contacto de tipo facturación electrónica, por favor verificar.'))     


# Detalle Movimiento
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal')
    
    #Cuenta analitica 
    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        if self.analytic_account_id:
            values = {
                    'analytic_tag_ids': [(5, 0, 0)],                
                }
            self.update(values)  
            
    #Etiqueta analitica
    @api.onchange('analytic_tag_ids')
    def _onchange_analytic_tag_ids(self):
        if self.analytic_tag_ids:
            values = {
                    'analytic_account_id': 0,                
                }
            self.update(values)  
        
        
    

