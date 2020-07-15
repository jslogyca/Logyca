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
class comercial_report(models.TransientModel):
    _name = 'logyca.comercial.report'
    _description = 'Reporte Comercial LOGYCA'

    ano_filter = fields.Integer(string='Año', required=True)      
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Proyección Ingresos - Año: {} ".format(record.ano_filter)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'RAZÓN SOCIAL,LÍNEA,FAMILIA,CUENTA,SERVICIO,SECTOR,COMERCIAL,CLIENTE,MOVIMIENTO,ENERO,FEBRERO,MARZO,ABRIL,MAYO,JUNIO,JULIO,AGOSTO,SEPTIEMBRE,OCTUBRE,NOVIEMBRE,DICIEMBRE,CAUSADO HOY, ASEGURADO AÑO'
        _columns = columns.split(",")
        return _columns
    
    #Ejecutar consulta SQL
    def run_sql(self):
        #Diferidos
        query_one = '''
            Select e."name" as company,coalesce(i."name",'-') as LineaAnalitica,coalesce(h."name",'-') as FamiliaAnalitica,coalesce(g."name",'-') as CuentaAnalitica,
                    coalesce(b."name",'-') as Servicio, coalesce(k."name",'-') as Sector,coalesce(n."name",'-') as Comercial,coalesce(j."name",'-') as Cliente,		
                    'Causación'as Movimiento,
                    Sum(case when extract(month from d."date") = 1 then d.amount_total else 0 end) as Enero,
                    Sum(case when extract(month from d."date") = 2 then d.amount_total else 0 end) as Febrero,
                    Sum(case when extract(month from d."date") = 3 then d.amount_total else 0 end) as Marzo,
                    Sum(case when extract(month from d."date") = 4 then d.amount_total else 0 end) as Abril,
                    Sum(case when extract(month from d."date") = 5 then d.amount_total else 0 end) as Mayo,
                    Sum(case when extract(month from d."date") = 6 then d.amount_total else 0 end) as Junio,
                    Sum(case when extract(month from d."date") = 7 then d.amount_total else 0 end) as Julio,
                    Sum(case when extract(month from d."date") = 8 then d.amount_total else 0 end) as Agosto,
                    Sum(case when extract(month from d."date") = 9 then d.amount_total else 0 end) as Septiembre,
                    Sum(case when extract(month from d."date") = 10 then d.amount_total else 0 end) as Octubre,
                    Sum(case when extract(month from d."date") = 11 then d.amount_total else 0 end) as Noviembre,
                    Sum(case when extract(month from d."date") = 12 then d.amount_total else 0 end) as Diciembre		
            From account_move a
            inner join account_move_line b on a.id = b.move_id
            inner join account_asset c on b.asset_id = c.id
            inner join account_move d on c.id = d.asset_id
            --Compañia
            inner join res_company e on a.company_id = e.id
            --Inf Analitica
            left join account_analytic_line f on b.id = f.move_id
            left join account_analytic_account g on f.account_id = g.id
            left join account_analytic_group h on g.group_id = h.id
            left join account_analytic_group i on h.parent_id = i.id
            --Tercero
            left join res_partner j on a.partner_id = j.id
            --Comercial
            left join sale_order l on a.invoice_origin = l."name"
            left join res_users m on l.user_id = m.id
            left join res_partner n on m.partner_id = n.id
            --Sector
            left join crm_team k on m.sale_team_id = k.id
            where a."type" in ('out_invoice','out_receipt','out_refund') and extract(year from d."date") = %s
            group by e."name",i."name",h."name",g."name",b."name",k."name",n."name",j."name"
        ''' % (self.ano_filter)
        
        #Facturación
        query_two = '''            
            Select e."name" as company,coalesce(i."name",'-') as LineaAnalitica,coalesce(h."name",'-') as FamiliaAnalitica,coalesce(g."name",'-') as CuentaAnalitica,
                    coalesce(b."name",'-') as Servicio, coalesce(k."name",coalesce(r."name",'-')) as Sector,coalesce(n."name",coalesce(q."name",'-')) as Comercial,coalesce(j."name",'-') as Cliente,	
                    'Facturación'as Movimiento,
                    Sum(case when extract(month from a."date") = 1 then a.amount_untaxed_signed else 0 end) as Enero,
                    Sum(case when extract(month from a."date") = 2 then a.amount_untaxed_signed else 0 end) as Febrero,
                    Sum(case when extract(month from a."date") = 3 then a.amount_untaxed_signed else 0 end) as Marzo,
                    Sum(case when extract(month from a."date") = 4 then a.amount_untaxed_signed else 0 end) as Abril,
                    Sum(case when extract(month from a."date") = 5 then a.amount_untaxed_signed else 0 end) as Mayo,
                    Sum(case when extract(month from a."date") = 6 then a.amount_untaxed_signed else 0 end) as Junio,
                    Sum(case when extract(month from a."date") = 7 then a.amount_untaxed_signed else 0 end) as Julio,
                    Sum(case when extract(month from a."date") = 8 then a.amount_untaxed_signed else 0 end) as Agosto,
                    Sum(case when extract(month from a."date") = 9 then a.amount_untaxed_signed else 0 end) as Septiembre,
                    Sum(case when extract(month from a."date") = 10 then a.amount_untaxed_signed else 0 end) as Octubre,
                    Sum(case when extract(month from a."date") = 11 then a.amount_untaxed_signed else 0 end) as Noviembre,
                    Sum(case when extract(month from a."date") = 12 then a.amount_untaxed_signed else 0 end) as Diciembre		
            From account_move a
            inner join account_move_line b on a.id = b.move_id
            --Compañia
            inner join res_company e on a.company_id = e.id
            --Inf Analitica
            inner join account_analytic_line f on b.id = f.move_id
            left join account_analytic_account g on f.account_id = g.id
            left join account_analytic_group h on g.group_id = h.id
            left join account_analytic_group i on h.parent_id = i.id
            --Tercero
            left join res_partner j on a.partner_id = j.id
            --Comercial
            left join sale_order l on a.invoice_origin = l."name"
            left join res_users m on l.user_id = m.id
            left join res_partner n on m.partner_id = n.id
            --Sector
            left join crm_team k on m.sale_team_id = k.id
            --Recurrentes
            left join sale_subscription o on a.invoice_origin = o.code
            left join res_users p on o.user_id = p.id
            left join res_partner q on p.partner_id = q.id
            left join crm_team r on p.sale_team_id = r.id   
            where a.state = 'posted' and a."type" in ('out_invoice','out_receipt','out_refund') and extract(year from a."date") = %s
            group by e."name",i."name",h."name",g."name",b."name",k."name",n."name",j."name",r."name",q."name"
        ''' % (self.ano_filter)
        
        #Suscripciones
        query_three = '''
            Select e."name" as company,coalesce(i."name",'-') as LineaAnalitica,coalesce(h."name",'-') as FamiliaAnalitica,coalesce(g."name",'-') as CuentaAnalitica,
                coalesce(b."name",'-') as Servicio, coalesce(k."name",'-') as Sector,coalesce(n."name",'-') as Comercial,coalesce(j."name",'-') as Cliente,	
                'Causación' as Movimiento,		
                Sum(case when 1 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Enero,		
                Sum(case when 2 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Febrero,
                Sum(case when 3 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Marzo,
                Sum(case when 4 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Abril,
                Sum(case when 5 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Mayo,
                Sum(case when 6 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Junio,
                Sum(case when 7 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Julio,
                Sum(case when 8 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Agosto,
                Sum(case when 9 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Septiembre,
                Sum(case when 10 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Octubre,
                Sum(case when 11 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Noviembre,
                Sum(case when 12 between extract(month from c.date_initial) and extract(month from c.date_finally) then c.recurring else 0 end) as Diciembre
            From account_move a
            inner join account_move_line b on a.id = b.move_id
            --Suscripciones
            inner join (select a.company_id,a.partner_id,a.code,a.date_start,a."date",a.user_id,
                        case when extract(year from a.date_start) != %s and extract(year from a.date_start) != extract(year from a."date"::date-'1 month'::interval) then cast(cast(extract(year from a."date"::date-'1 month'::interval) as varchar)||'-01-01' as date) else a.date_start end as date_initial,
			case when (extract(year from a.date_start) = %s and extract(year from a.date_start) != extract(year from a."date"::date-'1 month'::interval)) or a."date"::date-'1 month'::interval is null then cast(cast(extract(year from a.date_start)as varchar)||'-12-31'as date) else a."date"::date-'1 month'::interval end as date_finally,
                        sum(a.recurring_total) as recurring
                        from sale_subscription a
                        where extract(year from a.date_start) = %s or extract(year from a."date") = %s
                        group by a.company_id,a.partner_id,a.code,a.date_start,a."date",a.user_id) c on a.invoice_origin = c.code and a."date" = c.date_start
            --Compañia
            inner join res_company e on a.company_id = e.id
            --Inf Analitica
            inner join account_analytic_line f on b.id = f.move_id
            left join account_analytic_account g on f.account_id = g.id
            left join account_analytic_group h on g.group_id = h.id
            left join account_analytic_group i on h.parent_id = i.id
            --Tercero
            left join res_partner j on a.partner_id = j.id
            --Comercial
            left join res_users m on c.user_id = m.id
            left join res_partner n on m.partner_id = n.id
            --Sector
            left join crm_team k on m.sale_team_id = k.id
            where a.state = 'posted' and a."type" in ('out_invoice','out_receipt','out_refund')
            group by e."name",i."name",h."name",g."name",b."name",k."name",n."name",j."name"
        ''' % (self.ano_filter,self.ano_filter,self.ano_filter,self.ano_filter)
        
        #Fecha actual        
        date_today = fields.Date.context_today(self)
        
        #Consulta final
        query = '''
            Select Company,LineaAnalitica,FamiliaAnalitica,CuentaAnalitica,Servicio,Sector,Comercial,Cliente,Movimiento,
            Sum(Enero) as Enero,Sum(Febrero) as Febrero,Sum(Marzo) as Marzo,Sum(Abril) as Abril,Sum(Mayo) as Mayo,Sum(Junio) as Junio,
            Sum(Julio) as Julio,Sum(Agosto) as Agosto,Sum(Septiembre) as Septiembre,Sum(Octubre) as Octubre,Sum(Noviembre) as Noviembre,Sum(Diciembre) as Diciembre,		
            Sum(case when 1 <= extract(month from cast('%s' as date)) then Enero else 0 end +
            case when 2 <= extract(month from cast('%s' as date)) then Febrero else 0 end +
            case when 3 <= extract(month from cast('%s' as date)) then Marzo else 0 end +
            case when 4 <= extract(month from cast('%s' as date)) then Abril else 0 end +
            case when 5 <= extract(month from cast('%s' as date)) then Mayo else 0 end +
            case when 6 <= extract(month from cast('%s' as date)) then Junio else 0 end +
            case when 7 <= extract(month from cast('%s' as date)) then Julio else 0 end +
            case when 8 <= extract(month from cast('%s' as date)) then Agosto else 0 end +
            case when 9 <= extract(month from cast('%s' as date)) then Septiembre else 0 end +
            case when 10 <= extract(month from cast('%s' as date)) then Octubre else 0 end +
            case when 11 <= extract(month from cast('%s' as date)) then Noviembre else 0 end +
            case when 12 <= extract(month from cast('%s' as date)) then Diciembre else 0 end) As CausadoHoy,	
            Sum(Enero+Febrero+Marzo+Abril+Mayo+Junio+Julio+Agosto+Septiembre+Octubre+Noviembre+Diciembre) As AseguradoAño
            From
            (
                %s
                union
                %s
                union
                %s
            ) As A
            Where (Enero+Febrero+Marzo+Abril+Mayo+Junio+Julio+Agosto+Septiembre+Octubre+Noviembre+Diciembre) > 0
            Group By Company,LineaAnalitica,FamiliaAnalitica,CuentaAnalitica,Servicio,Sector,Comercial,Cliente,Movimiento
            Order By Company,LineaAnalitica,FamiliaAnalitica,CuentaAnalitica,Servicio,Sector,Comercial,Cliente,Movimiento
        '''  % (date_today,date_today,date_today,date_today,date_today,date_today,date_today,date_today,date_today,date_today,date_today,date_today,query_one,query_two,query_three)
        
        self._cr.execute(query)
        _res = self._cr.dictfetchall()
        return _res
    
    def get_excel(self):        
        
        result_columns = self.get_columns()
        result_query = self.run_sql()
            
        filename= 'Proyección Ingresos '+str(self.ano_filter)+'.xlsx'
        stream = io.BytesIO()
        book = xlsxwriter.Workbook(stream, {'in_memory': True})
        sheet = book.add_worksheet('BASE')
        
        #Estilos - https://xlsxwriter.readthedocs.io/format.html 
        
        ##Titulo
        title = 'Proyección Ingresos '+str(self.ano_filter)
        date_report = 'Generado '+str(fields.Date.context_today(self))
        cell_format_title = book.add_format({'bold': True})
        cell_format_title.set_font_name('Century Gothic')
        cell_format_title.set_font_size(20)
        sheet.merge_range('B2:D2', title, cell_format_title)
        sheet.write(1, 4, date_report)
        
        ##Encabezado
        cell_format_header = book.add_format({'bold': True, 'font_color': 'white'})
        cell_format_header.set_bg_color('#06496b')
        cell_format_header.set_font_name('Century Gothic')
        cell_format_header.set_font_size(10)
        cell_format_header.set_align('center')
        cell_format_header.set_align('vcenter')
        cell_format_header.set_text_wrap()
        sheet.set_row(4, 50)
        sheet.merge_range('C4:E4', 'INF. ANALÍTICA', cell_format_header)
        
        ##Detalle
        cell_format_det = book.add_format()
        cell_format_det.set_font_name('Century Gothic')
        cell_format_det.set_font_size(10)
        cell_format_det.set_bottom(1)
        cell_format_det.set_top(1)
        cell_format_det.set_text_wrap()
        
        ###Campos númericos
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
        for query in result_query: 
            for row in query.values(): 
                #Tamaño columna
                #tamaño = len(row)
                if aument_columns > 9:
                    sheet.write(aument_rows, aument_columns, row, number_format)
                else:                
                    sheet.write(aument_rows, aument_columns, row, cell_format_det)
                aument_columns = aument_columns + 1
            aument_rows = aument_rows + 1
            aument_columns = 1
        
        #Tamaño columnas
        sheet.set_column('B:D', 25)
        sheet.set_column('E:E', 30)
        sheet.set_column('F:F', 70)
        sheet.set_column('G:H', 25)
        sheet.set_column('I:I', 40)
        sheet.set_column('J:J', 20)
        sheet.set_column('K:X', 15)
        
        book.close()            
           
        self.write({
            'excel_file': base64.encodestring(stream.getvalue()),
            'excel_file_name': filename,
        })
            
        action = {
                    'name': 'ReporteComercial',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=logyca.comercial.report&id=" + str(self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                    'target': 'self',
                }
        return action
