# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
        columns = 'DOCUMENTO,AÑO,NÚMERO,FECHA DE FACTURA,NIT,ASOCIADO,REPRESENTANTE ANTE LOGYCA,CIUDAD,DIRECCIÓN,TELEFONO,MOVIL,EMAIL REPRESENTATE ANTE LOGYCA, EMAIL FACTURA ELECTRONICA,TIPO VINCULACIÓN,ACTIVOS,CUENTA POR PAGAR,FECHA VENCIMIENTO,PLAZOS DE PAGO,REFERENCIA,ORIGEN,VENDEDOR,CANTIDAD SIN IMPUESTOS,IMPUESTO,TOTAL,MONDO ADEUDADO,% ABONADO,DESCUENTO CONDICIONADO,TOTAL CON DESCUENTO,SIN IVA,PAGOS,DOCUMENTO PAGO,FECHA DEL PAGO, VALOR PAGADO'
        _columns = columns.split(",")
        return _columns
    
    def get_details(self):
        obj_account_moves = self.env['account.move'].search([('x_is_mass_billing', '=', True),('name','=','FEC/2020/230657')])
        lst_account_moves = []
        for move in obj_account_moves:
            #Documento, año y número de factura
            doc = move.name.split('/')[0]
            year = move.name.split('/')[1]
            num = move.name.split('/')[2]
            #Fecha de factura
            invoice_date = move.invoice_date
            #Cliente
            nit = move.partner_id.parent_id.vat
            partner = move.partner_id.parent_id.name
            #Representate ante logyca y contacto de factura electronica
            for client in move.partner_id.parent_id:
                for contacts in client.child_ids:
                    if contacts.x_contact_type.code == '002':
                        represent_logyca_name = contacts.name
                        represent_logyca_email = contacts.email
                    if contacts.x_contact_type.code == 'FE':
                        contact_fe = contacts.email                    
            #Datos de contacto
            city = move.partner_id.x_city.name
            street = move.partner_id.street
            phone = move.partner_id.phone
            mobile = move.partner_id.mobile
            #Tipo vinculación
            for client in move.partner_id.parent_id:
                vinculations = ''
                for vinculation in client.x_type_vinculation:
                    vinculations = vinculations +' | ' + vinculation.name
            #Activos
            asset_range = move.partner_id.parent_id.x_asset_range.name
            
            
            #Insertar 
            lst_move = [doc,year,num,invoice_date,nit,partner,represent_logyca_name,city,street,phone,mobile,represent_logyca_email,contact_fe,vinculations,asset_range]
            lst_account_moves.append(lst_move)
            
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
        title = 'Reporte CXC Facturación Masiva '+str(self.ano_filter)
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
                #if aument_columns > 9:
                sheet.write(aument_rows, aument_columns, row, number_format)
                #else:                
                #    sheet.write(aument_rows, aument_columns, row, cell_format_det)
                aument_columns = aument_columns + 1
            aument_rows = aument_rows + 1
            aument_columns = 1
        
        #Tamaño columnas
        #sheet.set_column('B:D', 25)
        #sheet.set_column('E:E', 30)
        #sheet.set_column('F:F', 70)
        #sheet.set_column('G:H', 25)
        #sheet.set_column('I:I', 40)
        #sheet.set_column('J:J', 20)
        #sheet.set_column('K:Y', 15)
        
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
