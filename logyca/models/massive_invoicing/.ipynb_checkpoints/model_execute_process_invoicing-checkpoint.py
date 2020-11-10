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
    type_vinculation = fields.Selection([
                                        ('1', 'Miembros'),
                                        ('2', 'Clientes'),                                        
                                        ('3', 'Otros'),                                        
                                    ], string='Tipo de vinculación')
    is_textil = fields.Boolean(string='Textileros')
    #Info Facturas
    cant_invoices = fields.Integer(string='Cantidad de facturas creadas', readonly=True)
        
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Facturación Masiva - {}".format(record.year)))
        return result
    
    #Creación facturas en estado borrador
    def create_invoicing_in_state_draft(self):
        if not self.type_vinculation:
            raise ValidationError(_("Debes seleccionar un tipo de vinculación"))             
        #Eliminar facturas masivas en estado borrador si ya existen
        #self.env['account.move'].search([('x_is_mass_billing', '=', True),('state','=','draft')]).unlink()
        #Obtener tipos de vinculación
        type_vinculation = []
        if self.type_vinculation == '1':
            obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])            
            for m in obj_type_vinculation_miembros:
                type_vinculation.append(m.id)
        if self.type_vinculation == '2':
            obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
            for c in obj_type_vinculation_cliente:
                type_vinculation.append(c.id)  
        #Obtener todas las ordenes de venta para confirmarlas y convertirlas en facturas
        code_textileros = 10
        if self.type_vinculation == '1' or self.type_vinculation == '2':
            if self.is_textil:
                sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','=',code_textileros)])
            else:
                sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','!=',code_textileros)])
        else:
            sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_gtin_massive_invoicing','=',True)])
        #,('state','not in',['sale','cancel'])
        cant = len(sales_order)
        #raise ValidationError(_(cant)) 
        for sale in sales_order:
            #Referencia
            ref = ''
            if sale.x_conditional_discount > 0:
                ref = 'Por pago de la factura antes de la fecha {} aplica un descuento al valor total de la factura de {} - No. Orden de venta {}.'.format(str(sale.x_conditional_discount_deadline),str(sale.x_conditional_discount),sale.name)
            else:
                ref = 'No. Orden de venta {}'.format(sale.name)
            
            #Campos de fac masiva
            values_update = {
                'x_is_mass_billing' : True,
                'ref': ref,
                'x_num_order_purchase': sale.name,
                'x_value_discounts' : sale.x_conditional_discount,
                'x_discounts_deadline' : sale.x_conditional_discount_deadline
            }
            #Confirmar orden de venta
            if sale.state != 'sale' and sale.state != 'cancel':
                sale.action_confirm()
            #Crear factura en estado borrador
            id_factura = sale._create_invoices()
            #Actualizar campos de Fac Masiva
            id_factura.update(values_update)
        
        self.cant_invoices = cant
        
    #Publicar facturas en estado borrador
    def public_invoicing_in_state_draft(self):
        code_textileros = 10
        #Obtener tipos de vinculación
        type_vinculation = []
        if self.type_vinculation == '1':
            obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])            
            for m in obj_type_vinculation_miembros:
                type_vinculation.append(m.id)
        if self.type_vinculation == '2':
            obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
            for c in obj_type_vinculation_cliente:
                type_vinculation.append(c.id)  
        #Traer facturas a publicar
        if self.type_vinculation == '1' or self.type_vinculation == '2':
            if self.is_textil:
                account_move = self.env['account.move'].search([('x_is_mass_billing', '=', True),('state','=','draft'),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','=',code_textileros)])
            else:
                account_move = self.env['account.move'].search([('x_is_mass_billing', '=', True),('state','=','draft'),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','!=',code_textileros)])
        else:
            account_move = self.env['account.move'].search([('x_is_mass_billing', '=', True),('state','=','draft'),('partner_id.parent_id.x_gtin_massive_invoicing','=',True)])
            
        for move in account_move:
          #Publicar factura
          move.action_post()
          values_update = {
            'x_studio_aprobada_para_pagar' : True
          }
          move.update(values_update)

            
