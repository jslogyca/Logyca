# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo ACCOUNT-MOVE/ MOVIMIENTO DETALLE-------------------------------#

class AccountMove(models.Model):
    _inherit = 'account.move'
    #PAÍS 
    x_country_account_id = fields.Many2one('res.country', string='País', track_visibility='onchange')
    #NUMERO DE ORDEN DE COMPRA
    x_num_order_purchase = fields.Char(string='Número orden de compra', track_visibility='onchange')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Posición fiscal', track_visibility='onchange')

    @api.onchange('partner_id')
    def _onchange_partner_id_country(self):
        
        partner = self.env['res.partner'].browse(self.partner_id.id)
        
        values = {
                'x_country_account_id': partner.country_id ,                
            }
        self.update(values)

    @api.onchange('invoice_origin')
    def _inherit_fiscal_position(self):        
        #sale_order = self.env['sale_order'].browse(self.invoice_origin.id)
        for move in self:
            self.env.cr.execute("Select B.fiscal_position_id From account_move a Inner join sale_order b on a.invoice_origin = b.name WHERE a.invoice_origin = '"+str(move.invoice_origin)+"'")
                
            fiscal_position_id = set(res[0] for res in self.env.cr.fetchall())

            values = {
                    'fiscal_position_id': fiscal_position_id ,                
                }

            self.update(values)
