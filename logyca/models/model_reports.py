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
        query = """select c."name" as cuenta,a."name" as contacto
                    from res_partner a
                    inner join logyca_contact_types_res_partner_rel b on a.id = b.res_partner_id and b.logyca_contact_types_id = 2
                    inner join res_partner c on a.parent_id = c.id and c.x_active_vinculation = true
                    inner join logyca_vinculation_types_res_partner_rel d on c.id = d.res_partner_id and d.logyca_vinculation_types_id in (1,2)"""
        
        query = self.query
        
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res

