# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
import xlsxwriter
import requests


class ReportIncomeReportWizard(models.TransientModel):
    _name = 'report.income.report.wizard'
    _description = 'Report Income Report Wizard'

    date_from = fields.Date(string='Fecha de Inicio')
    date_to = fields.Date(string='Fecha Fin')
    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")


    def do_report(self):
        value = self.get_values(self.date_from, self.date_to)
        if not value:
            raise ValidationError(_('!No hay resultados para los datos seleccionadoooooos¡'))
        self.make_file(value)

        if not self.data:
            raise UserError("No se generó el archivo correctamente.")

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=report.income.report.wizard&id={self.id}&field=data&filename_field=data_name&download=true",
            'target': 'self',
        }

    def get_values(self, date_from, date_to):
        value = []
        self._cr.execute(''' select p.vat,
                                    p.name,
                                    m.name,
                                    (select pt.name->>'es_CO'
                                    from account_move_line l
                                    inner join product_product pp ON pp.id = l.product_id
                                    inner join product_template pt on pp.product_tmpl_id = pt.id
                                    where l.move_id=m.id limit 1),
                                    red.name->>'es_CO',
                                    m.amount_untaxed, 
                                    to_char(m.date,'DD/MM/YYYY'),
                                    date_part('month',m.date)as mes_fact,
                                    date_part('year',m.date)as year_fact,
                                    c.name as company_id,
                                    up.name,
                                    team.name->>'es_CO',
                                    ma.name,
                                    ma.amount_total, 
                                    to_char(ma.date,'DD/MM/YYYY'),
                                    date_part('month',ma.date)as mes,
                                    date_part('year',ma.date)as year,
                                    ma.state,
                                    red.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' as plan
                                    from account_move m
                                    inner join account_move_deferred_rel aml on aml.original_move_id=m.id
                                    inner join account_move ma on ma.id=aml.deferred_move_id
                                    inner join res_company c on c.id=m.company_id
                                    inner join res_partner p on p.id=m.partner_id
                                    inner join res_users u on u.id=m.invoice_user_id
                                    inner join res_partner up on up.id=u.partner_id
                                    inner join crm_team team on team.id=m.team_id
                                    left join account_analytic_account red on red.id = m.analytic_account_id
                                    left JOIN account_analytic_plan pla on pla.id=red.plan_id                                   
                                    where m.date between %s and %s and m.state='posted'
                                    and m.move_type in ('out_invoice')
                                    order by p.id, m.id ''', 
                                    (date_from, date_to))
        
        lineas = self._cr.fetchall()
        return lineas

    def get_values_inv(self, date_from, date_to):
        value = []
        self._cr.execute(''' select p.vat,
                                    p.name,
                                    i.name,
                                    pt.name,
                                    red.name,
                                    i.amount_untaxed, 
                                    to_char(i.date,'DD/MM/YYYY'),
                                    date_part('month',i.date)as mes_fact,
                                    date_part('year',i.date)as year_fact,
                                    c.name as company_id,
                                    up.name,
                                    team.name,
                                    i.amount_total, 
                                    to_char(i.date,'DD/MM/YYYY'),
                                    date_part('month',i.date)as mes,
                                    date_part('year',i.date)as year,
                                    i.state,
                                    aaa.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' as plan
                                    from account_move_line l
                                    inner join account_move i on i.id=l.move_id
                                    left join asset_move_line_rel aml on aml.line_id = l.id
                                    left join account_asset a on a.id=aml.asset_id
                                    JOIN LATERAL jsonb_each(a.analytic_distribution) AS dist(key, value) ON TRUE
                                    LEFT JOIN account_analytic_account aaa ON aaa.id::text = key
                                    INNER JOIN account_analytic_plan pla on pla.id=aaa.plan_id
                                    inner join res_company c on c.id=i.company_id
                                    inner join res_partner p on p.id=i.partner_id
                                    inner join res_users u on u.id=i.invoice_user_id
                                    inner join res_partner up on up.id=u.partner_id
                                    inner join crm_team team on team.id=i.team_id
                                    inner join product_product pp ON pp.id = l.product_id
                                    inner join product_template pt on pp.product_tmpl_id = pt.id
                                    left join account_analytic_account red on red.id = i.analytic_account_id                                    
                                    where i.date between %s and %s and i.state='posted'
                                    and a.id is null and i.move_type in ('out_invoice')
                                    order by p.id, i.id ''', 
                                    (date_from, date_to))
        
        lineas_suscrip = self._cr.fetchall()
        return lineas_suscrip

    def make_file(self, value):
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        date_file = fields.Datetime.now()
        
        #formatos
        title_head = wb.add_format({
                        'bold': 1,
                        'border': 0,
                        'align': 'rigth',
                        'valign': 'vcenter'})
        title_head.set_font_name('Arial')
        title_head.set_font_size(10) 
        
        subtitle_head = wb.add_format({
                        'bold': 1,
                        'border': 1,
                        'align': 'rigth',
                        'fg_color': 'orange',
                        'valign': 'vcenter'})
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)
        
        user = self.env['res.users'].browse(self._uid)
        ws.write(0, 0, 'INGRESOS PROYECTADOS', title_head)
        ws.write(1, 0, str(user.company_id.name), title_head)
        ws.write(3, 0, 'Fecha Inicio', title_head)
        ws.write(3, 1, str(self.date_from))
        ws.write(4, 0, 'Fecha Inicio', title_head)
        ws.write(4, 1, str(self.date_to))
        ws.write(5, 0, 'Usuario', title_head)
        ws.write(5, 1, str(user.partner_id.name))
        ws.write(6, 0, 'Fecha Archivo', title_head)
        ws.write(6, 1, str(date_file))

        fila_title=9
        ws.write(fila_title, 0, 'NIT', subtitle_head)
        ws.write(fila_title, 1, 'Cliente', subtitle_head)
        ws.write(fila_title, 2, 'Factura', subtitle_head)
        ws.write(fila_title, 3, 'Producto', subtitle_head)
        ws.write(fila_title, 4, 'Red de Valor', subtitle_head)
        ws.write(fila_title, 5, 'Total Fact.', subtitle_head)
        ws.write(fila_title, 6, 'Fecha de la factura', subtitle_head)
        ws.write(fila_title, 7, 'Mes Fact', subtitle_head)
        ws.write(fila_title, 8, 'Año Fact', subtitle_head)
        ws.write(fila_title, 9, 'Compañía', subtitle_head)
        ws.write(fila_title, 10, 'Vendedor', subtitle_head)
        ws.write(fila_title, 11, 'Equipo de Venta', subtitle_head)
        ws.write(fila_title, 12, 'Diferido', subtitle_head)
        ws.write(fila_title, 13, 'Total Dif.', subtitle_head)
        ws.write(fila_title, 14, 'Fecha Dif', subtitle_head)
        ws.write(fila_title, 15, 'Mes Dif', subtitle_head)
        ws.write(fila_title, 16, 'Año Dif', subtitle_head)
        ws.write(fila_title, 17, 'Estado Dif', subtitle_head)
        ws.write(fila_title, 18, 'Cuenta Analítica', subtitle_head)

        fila=10
        invoice = None
        reg_initial = True
        for x in value:
            if reg_initial:
                ws.write(fila,0,x[0],title_head)
                ws.write(fila,1,x[1],title_head)
                ws.write(fila,2,x[2],title_head)
                ws.write(fila,3,x[3],title_head)
                ws.write(fila,4,x[4],title_head)
                ws.write(fila,5,x[5],title_head)
                ws.write(fila,6,x[6],title_head)
                ws.write(fila,7,x[7],title_head)
                ws.write(fila,8,x[8],title_head)
                ws.write(fila,9,x[9],title_head)
                ws.write(fila,10,x[10],title_head)
                ws.write(fila,11,'No Aplica',title_head)
                ws.write(fila,12,'No Aplica',title_head)
                ws.write(fila,13,'No Aplica',title_head)
                ws.write(fila,14,'No Aplica',title_head)
                ws.write(fila,15,'No Aplica',title_head)
                ws.write(fila,16,'No Aplica',title_head)
                ws.write(fila,17,x[17],title_head)
                reg_initial = False
                invoice = x[1]
                fila+=1
            if invoice == x[1]:
                ws.write(fila,0,x[0])
                ws.write(fila,1,x[1])
                ws.write(fila,2,x[2])
                ws.write(fila,3,x[3])
                ws.write(fila,4,x[4])
                ws.write(fila,5,x[5])
                ws.write(fila,6,x[6])
                ws.write(fila,7,x[7])
                ws.write(fila,8,x[8])
                ws.write(fila,9,x[9])
                ws.write(fila,10,x[10])
                ws.write(fila,11,x[11])
                ws.write(fila,12,x[12])
                ws.write(fila,13,x[13])
                ws.write(fila,14,x[14])
                ws.write(fila,15,x[15])
                ws.write(fila,16,x[16])
                ws.write(fila,17,x[17])
            else:
                ws.write(fila,0,x[0],title_head)
                ws.write(fila,1,x[1],title_head)
                ws.write(fila,2,x[2],title_head)
                ws.write(fila,3,x[3],title_head)
                ws.write(fila,4,x[4],title_head)
                ws.write(fila,5,x[5],title_head)
                ws.write(fila,6,x[6],title_head)
                ws.write(fila,7,x[7],title_head)
                ws.write(fila,8,x[8],title_head)
                ws.write(fila,9,x[9],title_head)
                ws.write(fila,10,x[10],title_head)
                ws.write(fila,11,'No Aplica',title_head)
                ws.write(fila,12,'No Aplica',title_head)
                ws.write(fila,13,'No Aplica',title_head)
                ws.write(fila,14,'No Aplica',title_head)
                ws.write(fila,15,'No Aplica',title_head)
                ws.write(fila,16,'No Aplica',title_head)
                ws.write(fila,17,x[17],title_head)
                fila+=1
                ws.write(fila,0,x[0])
                ws.write(fila,1,x[1])
                ws.write(fila,2,x[2])
                ws.write(fila,3,x[3])
                ws.write(fila,4,x[4])
                ws.write(fila,5,x[5])
                ws.write(fila,6,x[6])
                ws.write(fila,7,x[7])
                ws.write(fila,8,x[8])
                ws.write(fila,9,x[9])
                ws.write(fila,10,x[10])
                ws.write(fila,11,x[11])
                ws.write(fila,12,x[12])
                ws.write(fila,13,x[13])
                ws.write(fila,14,x[14])
                ws.write(fila,15,x[15])
                ws.write(fila,16,x[16])
                ws.write(fila,17,x[17])
            fila+=1
            invoice = x[1]

        # inv
        invoice = None
        reg_initial = True
        value_suscrip = self.get_values_inv(self.date_from, self.date_to)
        for x in value_suscrip:
            ws.write(fila,0,x[0],title_head)
            ws.write(fila,1,x[1],title_head)
            ws.write(fila,2,x[2],title_head)
            ws.write(fila,3,x[3],title_head)
            ws.write(fila,4,x[4],title_head)
            ws.write(fila,5,x[5],title_head)
            ws.write(fila,6,x[6],title_head)
            ws.write(fila,7,x[7],title_head)
            ws.write(fila,8,x[8],title_head)
            ws.write(fila,9,x[9],title_head)
            ws.write(fila,10,x[10],title_head)
            ws.write(fila,11,x[11],title_head)
            ws.write(fila,12,'No Aplica',title_head)
            ws.write(fila,13,'No Aplica',title_head)
            ws.write(fila,14,'No Aplica',title_head)
            ws.write(fila,15,'No Aplica',title_head)
            ws.write(fila,16,'No Aplica',title_head)
            ws.write(fila,17,x[16],title_head)
            ws.write(fila,18,x[17],title_head)
            reg_initial = False
            invoice = x[1]
            fila+=1

        try:
            wb.close()
            out = base64.b64encode(buf.getvalue())
            buf.close()
            safe_date = date_file.strftime('%Y-%m-%d_%H-%M-%S')
            self.data_name = f'IngresoProyectado-{safe_date}.xlsx'
            self.data = out
        except Exception as e:
            raise ValidationError(f'No se pudo generar el archivo: {e}')            
