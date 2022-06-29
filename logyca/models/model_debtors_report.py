# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

import xlwt
import base64
import io
import xlsxwriter
import requests
import logging

#---------------------------Modelo para generar REPORTES-------------------------------#

# Reportes
class comercial_report(models.TransientModel):
    _name = 'logyca.debtors.report'
    _description = 'Reporte Cartera LOGYCA'

    #report fields
    cut_off = fields.Date(string='Fecha Corte')
    company_id = fields.Many2one('res.company', string='Compañia')
    partner_id = fields.Many2one('res.partner', string='Cliente', domain=['|',['x_active_for_logyca', '=', True],['x_active_for_logyca', '=', False]])
    report_type = fields.Selection([
                                    ('1', 'Consolidado'),
                                    ('2', 'Detallado')     
                                    ], string='Tipo Reporte', default='1') 
    
    #excel fields
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name', size=64)
    
    def name_get(self):
        result = []
        for record in self:
            record_name = "Reporte Cartera - Al : {} ".format(record.cut_off) if record.cut_off else "Reporte Cartera"
            result.append((record.id, record_name ))
        return result
    
    #Retonar columnas
    def get_columns(self):
        # columns = 'DOC,FECHA EMISIÓN FACTURA,AÑO,FACTURA,DOC. IDENTIFICACIÓN,RAZON SOCIAL,CONTACTO FACTURA,NOMBRE DE PRODUCTO,VALOR ANTES DE IVA,IVA,TOTAL FACTURA,SALDO FACTURA,FECHA VENCIMIENTO,DÍAS CARTERA VENCIDA,MES VENCIMIENTO,RESPONSABLE,TIPO CARTERA,RED DE VALOR'
        columns = 'FECHA,AÑO,DOC,NRO,NIT,RAZON SOCIAL,PRODUCTO,VALOR,T. IVA,T. FACTURA,SALDO FACTURA,FECHA VENCIMIENTO,ACUERDO DE PAGO,DÍAS CARTERA VENCIDA,MES VENCIMIENTO,TIPO CARTERA,RESPONSABLE,EQUIPO DE VENTA,SEGUIMIENTO DE CARTERA, FECHA DE SEGUIMIENTO ULTIMO CONTACTO, ESTADO DE CARTERA, FECHA PROGRAMACIÓN PAGO'
        _columns = columns.split(",")
        return _columns
    
    def where(self):
        additional_query = ''
        
        if self.cut_off:
            additional_query += ' AND am.invoice_date <=  \'%s\' ' % str(self.cut_off)
        
        if self.company_id:
            additional_query += ' AND am.company_id = ' + str(self.company_id.id)
        
        if self.partner_id:
            additional_query += ' AND (am.partner_id = ' + str(self.partner_id.id) + ' OR rpp.id = ' + str(self.partner_id.id) + ')'
            
        if self.report_type == '1':
            additional_query += ' AND aml.id = (select id from account_move_line where move_id= am.id limit 1)'
        
        additional_query += ' ORDER BY "NRO" ASC;'
        
        return additional_query
    
    #Ejecutar consulta SQL
    def run_sql(self):
        
        where = str(self.where())
        
        #Consulta
        query = '''
            SELECT  to_char(am.date,'YYYY/MM/DD') as "FECHA",
                LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4) AS "AÑO",
                LEFT(am.name,3) AS "DOC", 
                RIGHT(am.name,6) AS "NRO",
                rp.vat AS "NIT",
                CASE WHEN rp.parent_id IS NULL 
                THEN rp.name 
                ELSE rpp.name
                END AS "RAZÓN SOCIAL",
                pt.name AS "PRODUCTO",
                am.amount_untaxed as "VALOR",
                am.amount_tax AS "T. IVA",
                am.amount_total AS "T. FACTURA",
                am.amount_residual AS "SALDO FACTURA",
                to_char(am.invoice_date_due,'YYYY/MM/DD') AS "FECHA VENCIMIENTO",
                apt.name AS "ACUERDO DE PAGO",
                CASE WHEN now() > am.invoice_date_due THEN DATE_PART('day', now() - am.invoice_date_due) ELSE 0 END AS "DÍAS CARTERA VENCIDA",
                SUBSTRING(TO_CHAR(am.invoice_date_due,'YYYY-MM-DD'),6,2) AS "MES VENCIMIENTO",
                CASE WHEN now() > am.invoice_date_due then 'VENCIDA ' || LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4)  else 'NO VENCIDA' END AS "TIPO CARTERA",
                rppp.name AS "RESPONSABLE",
                t.name AS "EQUIPO DE VENTA",
                am.x_debt_portfolio_monitoring AS "SEGUIMIENTO DE CARTERA",
                to_char(am.x_last_contact_debtor,'YYYY/MM/DD') AS "FECHA DE SEGUIMIENTO ULTIMO CONTACTO",
                dps.name AS "ESTADO DE CARTERA",
                to_char(am.x_estimated_payment_date,'YYYY/MM/DD') AS "FECHA PROGRAMACIÓN PAGO"
            FROM   account_move am
                LEFT JOIN account_analytic_account aaa ON aaa.id = am.analytic_account_id 
                INNER JOIN account_payment_term apt on apt.id = am.invoice_payment_term_id
                inner join crm_team t on t.id=am.team_id
                LEFT JOIN debtor_portfolio_status dps on dps.id=am.x_debtor_portfolio_status_id
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN res_partner rpp ON rpp.id = rp.parent_id
                LEFT JOIN res_users ru ON ru.id = am.invoice_user_id
                LEFT JOIN res_partner rppp ON ru.partner_id = rppp.id,
                account_move_line aml, product_product pp, product_template pt 
            WHERE 
                pp.product_tmpl_id = pt.id
                and aml.product_id= pp.id
                and am.id = aml.move_id  
                and am.state='posted' 
                and am.type='out_invoice'
                and (am.invoice_payment_state='not_paid' or am.invoice_payment_state='in_payment')
                and (am.name LIKE 'FEC%' or am.name LIKE 'FAC%' or am.name LIKE 'FAM%')
        '''  + str(self.where())
        
        logging.info(query)
        
        self._cr.execute(query)
        
        _res = self._cr.dictfetchall()
        return _res
    
    def get_excel(self):
        today = str(date.today())
        
        result_columns = self.get_columns()
        result_query = self.run_sql()
        
        name = "Reporte Cartera - Al : {} ".format(self.cut_off) if self.cut_off else "Reporte Cartera"
        filename= name + '.xlsx'
        stream = io.BytesIO()
        book = xlsxwriter.Workbook(stream, {'in_memory': True})
        sheet = book.add_worksheet('Reporte')
        
        #Estilos - https://xlsxwriter.readthedocs.io/format.html 
        
        #tipo reporte
        report_type = self.report_type
        if report_type == '1':
            report_type = 'CONSOLIDADO'
        else:
            report_type = 'DETALLADO'
        
        #si se filtra el cliente
        partner = self.partner_id
        if partner:
            partner = 'l cliente ' + str(self.partner_id.name)
        else:
            partner = ' todos los clientes'
            
        #compañia
        company = self.company_id
        if company:
            company = 'la compañía ' + str(self.company_id.name)
        else:
            company = 'todas las compañías'
            
        #usuario de la aplicacion
        user = self.env.uid
        user_name = str(self.env['res.users'].browse(user).partner_id.name)
        
        ##Titulo
        title = name
        report_details = 'Reporte de Cartera ' + report_type + ' de' + partner + ' de ' + company + ' - ' + 'Generado el ' + today + ' por ' + user_name
        cell_format_title = book.add_format({'bold': True})
        cell_format_title.set_font_name('Century Gothic')
        cell_format_title.set_font_size(12)
        sheet.merge_range('B2:D2', title, cell_format_title)
        sheet.write(1, 4, report_details)
        
        ##Encabezado
        cell_format_header = book.add_format({'bold': True, 'font_color': 'white'})
        cell_format_header.set_bg_color('#ff5900')
        cell_format_header.set_font_name('Century Gothic')
        cell_format_header.set_font_size(10)
        cell_format_header.set_align('center')
        cell_format_header.set_align('vcenter')
        cell_format_header.set_text_wrap()
        sheet.set_row(4, 50)
        sheet.merge_range('C4:E4', 'Facturas Pendientes de Pago', cell_format_header)
        
        ###Campos númericos
        number_format = book.add_format({'num_format': '#,##'})
        number_format.set_font_name('Century Gothic')
        number_format.set_font_size(10)        
        number_format.set_bottom(1)
        number_format.set_top(1)
        
        ###Campos fecha
        date_format = book.add_format({'num_format': 'dd/mm/yyyy'})
        date_format.set_font_name('Century Gothic')
        date_format.set_font_size(10)        
        date_format.set_bottom(1)
        date_format.set_top(1)
        
        #Agregar columnas
        aument_columns = 1
        for columns in result_columns:            
            sheet.write(4, aument_columns, columns, cell_format_header)
            aument_columns = aument_columns + 1

        #Agregar query
        aument_columns = 1
        aument_rows = 5
        for query in result_query: 
            for row in query.values(): 
                #Tamaño columna
                #tamaño = len(row)
                if aument_columns == 2 or aument_columns == 13:                
                    sheet.write(aument_rows, aument_columns, row, date_format)
                else:
                    sheet.write(aument_rows, aument_columns, row, number_format)
                aument_columns = aument_columns + 1
            aument_rows = aument_rows + 1
            aument_columns = 1
        
        #Tamaño columnas
        sheet.set_column('B:F', 15)
        sheet.set_column('G:I', 50)
        sheet.set_column('J:R', 15)
        sheet.set_column('S:S', 40)
        
        book.close()            
           
        self.write({
            'excel_file': base64.encodestring(stream.getvalue()),
            'excel_file_name': filename,
        })
            
        action = {
                    'name': 'ReporteCartera',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=logyca.debtors.report&id=" + str(self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                    'target': 'self',
                }
        return action
