# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
import xlsxwriter
import requests
#---------------------------Modelo para generar REPORTES-------------------------------#

# Reportes
class x_reports(models.Model):
    _name = 'logyca.reports'
    _description = 'Reportes creados por LOGYCA'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Char(string='Descripción', required=True)
    model = fields.Char(string='Modelo', required=True)
    columns = fields.Char(string='Columnas (Separadas por , )', required=True)
    query = fields.Text(string='Query')    
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name', size=64)
    
    
    #Retonar columnas
    def get_columns(self):
        _columns = self.columns.split(",")
        return _columns
    
    #Ejecutar consulta SQL
    def run_sql(self):
        query = self.query
        
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res
    
    def get_excel(self):        
        if self.query and self.columns:
            result_columns = self.get_columns()
            result_query = self.run_sql()
             
            filename= str(self.name)+'.xlsx'
            stream = io.BytesIO()
            book = xlsxwriter.Workbook(stream, {'in_memory': True})
            sheet = book.add_worksheet(str(self.name))

            #Agregar columnas
            aument_columns = 0
            for columns in result_columns:            
                sheet.write(0, aument_columns, columns)
                aument_columns = aument_columns + 1

            #Agregar query
            aument_columns = 0
            aument_rows = 1
            for query in result_query: 
                for row in query.values():                
                    sheet.write(aument_rows, aument_columns, row)
                    aument_columns = aument_columns + 1
                aument_rows = aument_rows + 1
                aument_columns = 0
            
            book.close()
            
            #self.excel_file = base64.encodestring(stream.getvalue())
            #self.excel_file_name = filename
            
            self.write({
                'excel_file': base64.encodestring(stream.getvalue()),
                # Filename = <siren>FECYYYYMMDD where YYYMMDD is the closing date
                'excel_file_name': filename,
            })
            
            action = {
                        'name': str(self.name),
                        'type': 'ir.actions.act_url',
                        'url': "web/content/?model=logyca.reports&id=" + str(self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                        'target': 'self',
                    }
            return action
        
# Reportes Contabilidad
class x_reports_account(models.Model):
    _name = 'logyca.reports.account'
    _description = 'Reportes creados por LOGYCA para Contabilidad'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Char(string='Descripción', required=True)    
    x_ano_initial = fields.Integer(string='Año Inicial', required=True)
    x_month_initial = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes Inicial', required=True)
    x_ano_finally = fields.Integer(string='Año Final', required=True)
    x_month_finally = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes Final', required=True)    
    columns = fields.Char(string='Columnas (Separadas por , )', required=True)
    query = fields.Text(string='Query')    
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name', size=64)
    
    
    #Retonar columnas
    def get_columns(self):
        _columns = self.columns.split(",")
        return _columns
    
    #Ejecutar consulta SQL
    def run_sql(self):
        #Armar fecha dependiendo lo seleccionado
        date_initial = str(self.x_ano_initial)+'-'+str(self.x_month_initial)+'-01'  # >=
        
        x_ano_finally = self.x_ano_finally
        x_month_finally = self.x_month_finally
        
        if x_month_finally == '12':
            x_ano_finally = x_ano_finally + 1 
            x_month_finally = 1
        else:
            x_month_finally = str(int(x_month_finally) + 1)

        date_finally = str(x_ano_finally)+'-'+str(x_month_finally)+'-01' # <
        
        query = self.query         
        query = query.replace("%s1", date_initial)
        query = query.replace("%s2", date_finally)
        
        #raise ValidationError(_(query))                
        
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res
    
    def get_excel(self):        
        if self.query and self.columns:
            result_columns = self.get_columns()
            result_query = self.run_sql()
             
            filename= str(self.name)+'.xlsx'
            stream = io.BytesIO()
            book = xlsxwriter.Workbook(stream, {'in_memory': True})
            sheet = book.add_worksheet(str(self.name))

            #Agregar columnas
            aument_columns = 0
            for columns in result_columns:            
                sheet.write(0, aument_columns, columns)
                aument_columns = aument_columns + 1

            #Agregar query
            aument_columns = 0
            aument_rows = 1
            for query in result_query: 
                for row in query.values():                
                    sheet.write(aument_rows, aument_columns, row)
                    aument_columns = aument_columns + 1
                aument_rows = aument_rows + 1
                aument_columns = 0
            
            book.close()
            
            #self.excel_file = base64.encodestring(stream.getvalue())
            #self.excel_file_name = filename
            
            self.write({
                'excel_file': base64.encodestring(stream.getvalue()),
                # Filename = <siren>FECYYYYMMDD where YYYMMDD is the closing date
                'excel_file_name': filename,
            })
            
            action = {
                        'name': str(self.name),
                        'type': 'ir.actions.act_url',
                        'url': "web/content/?model=logyca.reports.account&id=" + str(self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                        'target': 'self',
                    }
            return action
        
