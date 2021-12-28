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
    state_process = fields.Char(String='Estado del proceso', readonly=True)
    state_process_publish = fields.Char(String='Estado del proceso 2', readonly=True)
        
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
                sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','=',code_textileros),('invoice_status','!=','invoiced'),('state','=','draft')])
            else:
                sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_type_vinculation','in',type_vinculation),('partner_id.parent_id.x_sector_id.id','!=',code_textileros),('invoice_status','!=','invoiced'),('state','=','draft')])
                if not sales_order:
                    sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.x_type_vinculation','in',type_vinculation),('partner_id.x_sector_id.id','!=',code_textileros),('invoice_status','!=','invoiced'),('state','=','draft')])
        else:
            sales_order = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year)),('partner_id.parent_id.x_gtin_massive_invoicing','=',True),('invoice_status','!=','invoiced'),('state','=','draft')])
        #,('state','not in',['sale','cancel'])
        cant = len(sales_order)
        print('CANTIDAD COTIZACIONES', cant)
        #raise ValidationError(_(cant)) 
        for sale in sales_order:
            #Referencia
            ref = ''
            if sale.x_conditional_discount > 0:
                ref = 'Por pago de la factura antes de la fecha {} aplica un descuento al valor total de la factura de ${:,.2f}'.format(str(sale.x_conditional_discount_deadline),sale.x_conditional_discount)
            else:
                for line in sale.order_line:
                    if line.discount > 0:
                        value_discount = (line.price_unit / 100)*line.discount
                        if self.type_vinculation == '1':
                            ref = 'Entendiendo los retos económicos que están afrontando las empresas por el nuevo entorno que trae el post COVID, {} facturado a los miembros de LOGYCA / ASOCIACION en el año {} tiene un descuento de ${:,.2f}'.format(line.product_id.name,self.year,value_discount)
                        if self.type_vinculation == '2':
                            ref = 'Entendiendo los retos económicos que están afrontando las empresas por el nuevo entorno que trae el post COVID, {} facturado a los clientes de LOGYCA / ASOCIACION en el año {} tiene un descuento de ${:,.2f}'.format(line.product_id.name,self.year,value_discount)                        
                        if ref == '':
                            ref = '.'
                    else:
                        if ref == '':
                            ref = '.'         
            #Plazo de pago
            id_payment_term = 0
            obj_account_payment_term = self.env['account.payment.term'].search([('x_is_mass_billing', '=', True)])            
            for i in obj_account_payment_term:
                id_payment_term = i.id

            if id_payment_term == 0:
                raise ValidationError(_('No esta configurado un plazo de pago valido para facturación masiva')) 
            
            #Campos de fac masiva
            values_update = {
                'x_is_mass_billing' : True,
                'ref': ref,
                'invoice_payment_term_id':id_payment_term,
                'x_num_order_purchase': '.',
                'x_value_discounts' : sale.x_conditional_discount,
                'x_discounts_deadline' : sale.x_conditional_discount_deadline
            }
            print('CAMPOS DE LA FACTURA', values_update, sale)      
            #Confirmar orden de venta
            if sale.state != 'sale' and sale.state != 'cancel':
                sale.action_confirm()
            #Crear factura en estado borrador
            id_factura = sale._create_invoices()
            #Actualizar campos de Fac Masiva
            id_factura.update(values_update)
            self.env.cr.commit()
            print('CAMPOS DE LA FACTURA 3333333333', id_factura, sale)
        print('CANTIDAD 2222 COTIZACIONES', cant)
        self.cant_invoices = cant
        self.state_process = 'Se crearon las facturas en estado borrador correctamente.'
        self.state_process_publish = ''
        
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
        
        self.state_process_publish = 'Se publicaron las facturas correctamente.'