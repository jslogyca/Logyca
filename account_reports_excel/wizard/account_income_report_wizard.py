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



    date_from = fields.Date(string='Fecha de Inicio')
    date_to = fields.Date(string='Fecha Fin')
    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")


    def do_report(self):
        value = self.get_values(self.date_from, self.date_to)
        if not value:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))
        self.make_file(value)

        path = "/web/binary/download_document?"
        model = "report.income.report.wizard"
        filename = self.data_name

        url = path + "model={}&id={}&filename={}.xlsx".format(
            model, self.id, filename)

        return {
            'type' : 'ir.actions.act_url',
            'url': url,
            'target': 'self',
            'tag': 'reload',
        }           


    def get_values(self, date_from, date_to):
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
                                    m.name,
                                    m.amount_total, 
                                    to_char(m.date,'DD/MM/YYYY'),
                                    date_part('month',m.date)as mes,
                                    date_part('year',m.date)as year,
                                    m.state,
                                    ca.name
                                    from account_move m
                                    inner join account_move_line l on l.asset_id=m.asset_id
                                    inner join account_asset a on a.id=l.asset_id
                                    inner join account_analytic_account ca on ca.id=a.account_analytic_id
                                    inner join account_move i on i.id=l.move_id
                                    inner join res_company c on c.id=m.company_id
                                    inner join res_partner p on p.id=i.partner_id
                                    inner join res_users u on u.id=i.invoice_user_id
                                    inner join res_partner up on up.id=u.partner_id
                                    inner join crm_team team on team.id=i.team_id
                                    inner join product_product pp ON pp.id = l.product_id
                                    inner join product_template pt on pp.product_tmpl_id = pt.id
                                    left join account_analytic_account red on red.id = i.analytic_account_id                                    
                                    where l.exclude_from_invoice_tab is False and i.date between %s and %s and i.state='posted'
                                    and a.asset_type = 'sale'
                                    order by p.id, m.id''', 
                                    (date_from, date_to))
        
        lineas = self._cr.fetchall()
        return lineas

    def get_values_suscrip(self, date_from, date_to):
        value = []
        self._cr.execute(''' SELECT p.vat,
                                    p.name,
                                    s.code,
                                    pt.name,
                                    red.name,
                                    so.amount_untaxed,
                                    to_char(so.date_order,'DD/MM/YYYY'),
                                    date_part('month',so.date_order)as mes_fact,
                                    date_part('year',so.date_order)as year_fact,
                                    c.name as company_id,
                                    up.name,
                                    team.name,
                                    m.name,
                                    m.amount_total, 
                                    to_char(m.date,'DD/MM/YYYY'),
                                    date_part('month',m.date)as mes,
                                    date_part('year',m.date)as year,
                                    m.state,
                                    ca.name
                                    FROM sale_subscription s
                                    INNER JOIN sale_subscription_line ls on ls.analytic_account_id=s.id
                                    INNER JOIN sale_subscription_stage e on e.id=s.stage_id
                                    inner join res_partner p on p.id=s.partner_id
                                    inner join product_product pp ON pp.id = ls.product_id
                                    inner join product_template pt on pp.product_tmpl_id = pt.id
                                    inner join sale_order_line l on l.subscription_id=s.id
                                    inner join sale_order so on so.id=l.order_id
                                    inner join res_company c on c.id=so.company_id
                                    inner join res_users u on u.id=so.user_id
                                    inner join res_partner up on up.id=u.partner_id
                                    inner join crm_team team on team.id=so.team_id
                                    inner join account_move_line li on li.subscription_id = s.id
                                    inner join account_move m on m.id=li.move_id
                                    left join account_analytic_account red on red.id = so.analytic_account_id
                                    left join account_analytic_account ca on ca.id=s.analytic_account_id
                                    WHERE e.in_progress is True and m.state='posted' 
                                    and so.date_order BETWEEN %s and %s
                                    order by p.id, s.id ''', 
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

        # suscripciones
        invoice = None
        reg_initial = True
        value_suscrip = self.get_values_suscrip(self.date_from, self.date_to)
        for x in value_suscrip:
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

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'IngresoProyectado' + '-' + str(date_file)
        except ValueError:
            raise Warning('No se pudo generar el archivo')
