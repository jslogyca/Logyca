 # -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import io
import requests
import json

#---------------------------------- Ejecucón del proceso - Facturación masiva
class x_MassiveInvoicingProcess(models.TransientModel):
    _name = 'massive.invoicing.process.fac'
    _description = 'Massive Invoicing - Execute Process'
    
    year = fields.Integer(string='Año proceso', required=True)
    #Facturas
    x_partner_accountmove = fields.One2many('massive.invoicing.partner.accountmove', 'process_id', string = 'Facturas', readonly=True)
        
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Facturación Masiva - {}".format(record.year)))
        return result
    
    #Creación facturas en estado borrador
    def create_invoicing_in_state_draft(self):   
        #Eliminar facturas masivas en estado borrador si ya existen
        accountmove_exists = self.env['account.move'].search([('x_is_mass_billing', '=', True),('state','=','draft')])
        accountmove_exists.unlink() 
        process_partneraccountmove_exists = self.env['massive.invoicing.partner.accountmove'].search([('process_id', '=', self.id)])
        process_partneraccountmove_exists.unlink()
        #Obtener todas las ordenes de venta para confirmarlas y convertirlas en facturas
        sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('state','not in',['sale','cancel'])])
        #raise ValidationError(_(len(sales_order))) 
        #cant = 0
        for sale in sales_order:
            #cant = cant + 1
            #if cant == 800:
            #    break
            #Confirmar orden de venta
            sale.action_confirm()
            #Crear factura en estado borrador
            id_factura = sale._create_invoices()
            #Actualizar campos de Fac Masiva
            values_update = {
                'x_is_mass_billing' : True,
                'x_value_discounts' : sale.x_conditional_discount,
                'x_discounts_deadline' : sale.x_conditional_discount_deadline
            }
            id_factura.update(values_update)
            #Obtener Id Compañia
            partner_id = 0
            vat = ''
            if sale.partner_id.parent_id.id:
                partner_id = sale.partner_id.parent_id.id
                vat = sale.partner_id.parent_id.vat
            else:
                partner_id = sale.partner_id.id
                vat = sale.partner_id.vat
            #Guardar en tabla intermedia las facturas creadas para consultarlas de forma rapida
            process_partneraccountmove = self.env['massive.invoicing.partner.accountmove'].search([('process_id', '=', self.id),('partner_id','=',partner_id)])
            if not process_partneraccountmove:
                values_save_process = {
                    'process_id' : self.id,
                    'partner_id' : partner_id,
                    'vat' : vat,
                    'invoice_one' : id_factura.id                                              
                }            
                process_partneraccountmove_create = self.env['massive.invoicing.partner.accountmove'].create(values_save_process)
            else:
                values_update_process = {
                    'invoice_two' : id_factura.id                                              
                }
                process_partneraccountmove.update(values_update_process)
            

class x_MassiveInvoicingPartnerAccountMove(models.TransientModel):
    _name = 'massive.invoicing.partner.accountmove'
    _description = 'Massive Invoicing - Partner Account Move'
    
    process_id = fields.Many2one('massive.invoicing.process.fac',string='Proceso FacMasiva', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Compañía', required=True)
    type_vinculation = fields.Many2many(string='Tipo de vinculación', readonly=True, related='partner_id.x_type_vinculation')    
    sector = fields.Many2one(string='Sector', readonly=True, related='partner_id.x_sector_id')    
    vat = fields.Char(string='Nit', required=True)
    invoice_one = fields.Many2one('account.move', string='Factura #1', readonly=True)
    invoice_two = fields.Many2one('account.move', string='Factura #2', readonly=True)
