# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
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
    

    
    
