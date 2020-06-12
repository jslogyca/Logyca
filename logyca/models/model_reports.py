# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
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

            filename= str(self.name)+'.xls'
            stream = io.BytesIO()
            book = xlwt.Workbook(encoding='utf-8')
            sheet = book.add_sheet(u'Sheet1')

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

            book.save(stream)

            self.excel_file = base64.encodestring(stream.getvalue())
            self.excel_file_name = filename
        
        
