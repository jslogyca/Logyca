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
        self._cr.execute(''' select p.name,
                                    i.name,
                                    i.amount_total, 
                                    to_char(i.date,'DD/MM/YYYY'),
                                    c.name as company_id,
                                    m.name,
                                    m.amount_total, 
                                    to_char(m.date,'DD/MM/YYYY'),
                                    date_part('month',m.date)as mes,
                                    m.state
                                    from account_move m
                                    inner join account_move_line l on l.asset_id=m.asset_id
                                    inner join account_move i on i.id=l.move_id
                                    inner join res_company c on c.id=m.company_id
                                    inner join res_partner p on p.id=i.partner_id
                                    where l.exclude_from_invoice_tab is False and i.date between %s and %s
                                    order by p.id, m.id''', 
                                    (date_from, date_to))
        
        lineas = self._cr.fetchall()
        return lineas

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
        ws.write(fila_title, 0, 'Cliente', subtitle_head)
        ws.write(fila_title, 1, 'Factura', subtitle_head)
        ws.write(fila_title, 2, 'Total Fact.', subtitle_head)
        ws.write(fila_title, 3, 'Fecha de la factura', subtitle_head)
        ws.write(fila_title, 4, 'Compañía', subtitle_head)
        ws.write(fila_title, 5, 'Diferido', subtitle_head)
        ws.write(fila_title, 6, 'Total Dif.', subtitle_head)
        ws.write(fila_title, 7, 'Fecha Dif', subtitle_head)
        ws.write(fila_title, 8, 'Mes', subtitle_head)        
        ws.write(fila_title, 9, 'Estado Dif', subtitle_head)   

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
                reg_initial = False
                invoice = x[1]
                fila+=1
            if invoice == x[1]:
                ws.write(fila,5,x[5])
                ws.write(fila,6,x[6])
                ws.write(fila,7,x[7])
                ws.write(fila,8,x[8])
                ws.write(fila,9,x[9])
            else:
                ws.write(fila,0,x[0],title_head)
                ws.write(fila,1,x[1],title_head)
                ws.write(fila,2,x[2],title_head)
                ws.write(fila,3,x[3],title_head)
                ws.write(fila,4,x[4],title_head)
                fila+=1
                ws.write(fila,5,x[5])
                ws.write(fila,6,x[6])
                ws.write(fila,7,x[7])
                ws.write(fila,8,x[8])
                ws.write(fila,9,x[9])                
            fila+=1
            invoice = x[1]
        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'FacturaXproducto' + '-' + str(date_file)
        except ValueError:
            raise Warning('No se pudo generar el archivo')
