# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

import xlwt
import base64
import io
import xlsxwriter
import requests

#---------------------------Modelo para generar REPORTES CXC FAC MASIVA-------------------------------#

# Reportes
class MassiveInvoicingCXC_report(models.TransientModel):
    _name = 'massive.invoicing.report.cxc'
    _description = 'Reporte CXC Facturación Masiva'

    ano_filter = fields.Integer(string='Año', required=True)      
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Reporte CXC Facturación Masiva - Año: {} ".format(record.ano_filter)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'DOCUMENTO,AÑO,NÚMERO,FECHA DE FACTURA,NIT,RAZÓN SOCIAL,SECTOR,REPRESENTANTE ANTE LOGYCA,CIUDAD,DIRECCIÓN,TELEFONO,MOVIL,EMAIL REPRESENTATE ANTE LOGYCA, EMAIL FACTURA ELECTRONICA,TIPO VINCULACIÓN,ACTIVOS,CUENTA POR PAGAR,FECHA VENCIMIENTO,PLAZOS DE PAGO,REFERENCIA,ORIGEN,VENDEDOR,PRODUCTO,CANTIDAD,PRECIO UNITARIO,SUBTOTAL,IMPUESTOS,TOTAL,DESCUENTO (%),DCTO CONDICIONADO,RECAUDADO ANTES DE IVA,CXC ANTES DE IVA,ESTADO,CUENTA ANALÍTICA,PAGOS,DOCUMENTO PAGO,FECHA DEL PAGO, VALOR PAGADO'
        #CANTIDAD SIN IMPUESTOS,IMPUESTO,TOTAL,MONDO ADEUDADO,% ABONADO,DESCUENTO CONDICIONADO,TOTAL CON DESCUENTO,SIN IVA,
        _columns = columns.split(",")
        return _columns
    
    def get_details(self):
        #names = ['FEC/2020/231112','FEC/2020/231113']
        #obj_account_moves = self.env['account.move'].search([('x_is_mass_billing', '=', True),('name','in',names)])
        date_initial_filter = datetime.strptime(str(self.ano_filter)+'-01-01','%Y-%m-%d')
        date_finally_filter = datetime.strptime(str(self.ano_filter)+'-12-31','%Y-%m-%d')
        obj_account_moves = self.env['account.move'].search([('x_is_mass_billing', '=', True),('type','=','out_invoice'),('invoice_date','>=',date_initial_filter),('invoice_date','<=',date_finally_filter)]) 
        #raise ValidationError(_(obj_account_moves))
        lst_account_moves = []
        for move in obj_account_moves:
            #try:
                #Determinar el cliente de la factura
                if move.partner_id.parent_id:
                    partner_id = move.partner_id.parent_id
                else:
                    partner_id = move.partner_id

                #Documento, año y número de factura
                doc = move.name.split('/')[0]
                year = move.name.split('/')[1]
                num = move.name.split('/')[2]
                #Fecha de factura
                invoice_date = str(move.invoice_date)
                #Cliente
                nit = partner_id.vat
                partner = partner_id.name
                #Representate ante logyca y contacto de factura electronica
                for client in partner_id:
                    for contacts in client.child_ids:
                        for contact_type in contacts.x_contact_type:
                            if contact_type.code == '002':
                                represent_logyca_name = contacts.name
                                represent_logyca_email = contacts.email
                            if contact_type.code == 'FE':
                                contact_fe = contacts.email
                
                #represent_logyca_name = move.partner_id.name                    
                #Datos de contacto
                city = move.partner_id.x_city.name
                street = move.partner_id.street
                phone = move.partner_id.phone
                mobile = move.partner_id.mobile
                classification = partner_id.x_sector_id.name
                #Tipo vinculación
                for client in partner_id:
                    vinculations = ''
                    for vinculation in client.x_type_vinculation:
                        if vinculations == '':
                            vinculations = vinculation.name
                        else:
                            vinculations = vinculations +', ' + vinculation.name
                #Activos
                asset_range = partner_id.x_asset_range.name
                #Cuenta
                for line in move.line_ids:
                    if line.debit > 0:
                        account = line.account_id.display_name
                #Fecha de vencimiento y plazo de pago
                date_due = str(move.invoice_date_due)
                payment_term = move.invoice_payment_term_id.name
                #Referencia, orgin y vendedor
                ref = move.ref
                origin = move.invoice_origin
                salesperson = move.invoice_user_id.name
                #---------Valores Generales
                #Cantidad sin impuestos
                amount_untaxed = move.amount_untaxed
                #Impuesto
                amount_tax = move.amount_tax
                #Total
                amount_total = move.amount_total
                #Monto adeudado firnamo y % Abonado
                amount_owed = move.amount_residual_signed
                if amount_owed > 0:
                    percentage_owed = 100-((amount_owed/amount_total)*100)
                else:
                    percentage_owed = 0
                #Descuento condicionado
                value_discount = move.x_value_discounts
                #Total con descuento
                amount_total_with_discount = move.x_amount_total_discounts
                #Sin IVA
                without_iva = amount_untaxed-value_discount
                #------------Info pagos
                invoice_payments_widget = move.invoice_payments_widget
                paid = move.invoice_payment_state
                reconciled_info = move._get_reconciled_info_JSON_values()
                document_paid = ''
                date_paid = ''
                value_paid = 0
                for payments in reconciled_info:
                    obj_payment = self.env['account.move'].search([('id', '=', payments.get('move_id'))])
                    #raise ValidationError(_(obj_payment))
                    if document_paid == '':
                        document_paid = obj_payment.name
                        date_paid = str(obj_payment.date)
                    else:
                        document_paid = document_paid +' - '+ obj_payment.name
                        date_paid = str(date_paid) +' | '+ str(obj_payment.date)
                    value_paid = value_paid + obj_payment.amount_total                
                #---------Items de la factura
                for items in move.invoice_line_ids:
                    #Producto
                    product = items.product_id.display_name
                    #Cantidad
                    quantity = items.quantity
                    #Precio unitario
                    price_unit = items.price_unit
                    #Subtotal
                    price_subtotal = items.price_subtotal
                    #--------Info descuento y recaudo
                    porcentage_discount = 0
                    discount = 0
                    collected_value = 0
                    value_cxc = price_subtotal
                    if value_paid > 0:
                        if move.x_discount_payment:
                            #Descuento %
                            porcentage_discount = (price_subtotal/amount_untaxed)*100
                            #Descuento condicionado
                            discount = (value_discount/100)*porcentage_discount
                            #Recaudo
                            collected_value = price_subtotal-discount
                            #CXC
                            value_cxc = price_subtotal-discount-collected_value
                        else:
                            #Descuento %
                            porcentage_discount = 0
                            #Descuento condicionado
                            discount = 0
                            if percentage_owed > 0:
                                #Recaudo
                                collected_value = (price_subtotal/100)*percentage_owed
                                #CXC
                                value_cxc = price_subtotal-collected_value
                            else:
                                #Recaudo
                                collected_value = price_subtotal
                                #CXC
                                value_cxc = price_subtotal
                    #--------Info final
                    #Impuestos
                    tax = items.tax_ids.display_name
                    #Total
                    price_total = items.price_total
                    #Estado
                    state = items.parent_state
                    #Cuenta analitica
                    analytic_account = items.analytic_account_id.display_name

                    #------Insertar datos obtenidos
                    lst_move = [doc,year,num,invoice_date,nit,partner,classification,represent_logyca_name,city,street,phone,mobile,represent_logyca_email,contact_fe,vinculations,asset_range,account,date_due,payment_term,ref,origin,
                                salesperson,product,quantity,price_unit,price_subtotal,tax,price_total,porcentage_discount,discount,collected_value,value_cxc,state,analytic_account,paid,document_paid,date_paid,value_paid]
                    lst_account_moves.append(lst_move)
            #except Exception as e:
                #raise ValidationError(_(e))
                #raise ValidationError(_('La factura '+move.name+' esta causando problemas al generar el reporte, Msg Error: '+str(e)))
            
        #raise ValidationError(_(lst_account_moves))        
        return lst_account_moves
    
    def get_excel(self):        
        
        result_columns = self.get_columns()
        result_details = self.get_details()
            
        filename= 'Reporte CXC Facturación Masiva '+str(self.ano_filter)+'.xlsx'
        stream = io.BytesIO()
        book = xlsxwriter.Workbook(stream, {'in_memory': True})
        sheet = book.add_worksheet('FacMasiva-'+str(self.ano_filter))
        
        #Estilos - https://xlsxwriter.readthedocs.io/format.html 
        
        ##Titulo
        title = 'Reporte CXC'
        date_report = 'Generado '+str(fields.Date.context_today(self))
        cell_format_title = book.add_format({'bold': True})
        cell_format_title.set_font_name('Century Gothic')
        cell_format_title.set_font_size(20)
        sheet.merge_range('B2:D2', title, cell_format_title)
        sheet.write(1, 4, date_report)
        
        #Encabezado
        cell_format_header = book.add_format({'bold': True, 'font_color': 'white'})
        cell_format_header.set_bg_color('#06496b')
        cell_format_header.set_font_name('Century Gothic')
        cell_format_header.set_font_size(10)
        cell_format_header.set_align('center')
        cell_format_header.set_align('vcenter')
        cell_format_header.set_text_wrap()
        #sheet.set_row(4, 50)
        #sheet.merge_range('C4:E4', 'INF. ANALÍTICA', cell_format_header)
        
        #Detalle
        cell_format_det = book.add_format()
        cell_format_det.set_font_name('Century Gothic')
        cell_format_det.set_font_size(10)
        cell_format_det.set_bottom(1)
        cell_format_det.set_top(1)
        cell_format_det.set_text_wrap()
        
        #Campos númericos
        number_format = book.add_format({'num_format': '#,##'})
        number_format.set_font_name('Century Gothic')
        number_format.set_font_size(10)        
        number_format.set_bottom(1)
        number_format.set_top(1)        
        
        #Agregar columnas
        aument_columns = 1
        for columns in result_columns:            
            sheet.write(4, aument_columns, columns, cell_format_header)
            aument_columns = aument_columns + 1
        
        #Agregar query
        aument_columns = 1
        aument_rows = 5
        for details in result_details: 
            for row in details: 
                if aument_columns in [24,25,27,29,30,31,37]:
                    sheet.write(aument_rows, aument_columns, row, number_format)
                else:                
                    sheet.write(aument_rows, aument_columns, row, cell_format_det)
                aument_columns = aument_columns + 1
            aument_rows = aument_rows + 1
            aument_columns = 1
        
        #Tamaño columnas
        sheet.set_column('B:D', 15)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 15)
        sheet.set_column('G:G', 40)
        sheet.set_column('H:H', 25)
        sheet.set_column('I:I', 40)
        sheet.set_column('J:J', 15)
        sheet.set_column('K:K', 30)
        sheet.set_column('L:L', 15)
        sheet.set_column('M:M', 20)
        sheet.set_column('N:N', 30)
        sheet.set_column('O:O', 40)
        sheet.set_column('P:T', 20)
        sheet.set_column('U:U', 60)
        sheet.set_column('V:V', 20)
        sheet.set_column('W:W', 20)
        sheet.set_column('X:X', 40)
        sheet.set_column('Y:AD', 16)
        sheet.set_column('AE:AF', 30)
        sheet.set_column('AG:AH', 16)
        sheet.set_column('AI:AI', 30)
        sheet.set_column('AJ:AJ', 20)
        sheet.set_column('AK:AN', 16)
        
        book.close()            
           
        self.write({
            'excel_file': base64.encodestring(stream.getvalue()),
            'excel_file_name': filename,
        })
            
        action = {
                    'name': 'ReporteCXCFacMasiva',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=massive.invoicing.report.cxc&id=" + str(self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                    'target': 'self',
                }
        return action
