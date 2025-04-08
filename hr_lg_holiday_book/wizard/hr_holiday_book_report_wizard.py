# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
import xlsxwriter
import requests


class hr_holiday_book_report_wizard(models.TransientModel):
    _name = 'hr.holiday.book.report.wizard'
    _description = 'Holiday Book Report Wizard'
    

    date_to = fields.Date(string='Fecha Fin')
    employee_ids = fields.Many2many('hr.employee', 'employee_holidays_wizard_rel',
        'wizard_id', 'employee_id', string='Employees')
    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    def do_report(self):
        value = self.get_values()
        if not value:
            raise ValidationError(_('!No hay resultados para los datos seleccionados¡'))
        self.make_file(value)

        path = "/web/binary/download_document?"
        model = "hr.holiday.book.report.wizard"
        filename = self.data_name

        url = path + "model={}&id={}&filename={}.xlsx".format(
            model, self.id, filename)

        return {
            'type' : 'ir.actions.act_url',
            'url': url,
            'target': 'self',
            'tag': 'reload',
        }           


    def get_values(self):
        value = []
        if self.employee_ids:
            self._cr.execute(''' SELECT 
                                    e.identification_id, 
                                    e.name, 
                                    to_char(c.date_start,'YYYY/MM/DD'),
                                    h.id,
                                    CASE WHEN g.code is not null
                                    THEN g.code
                                    ELSE 'No existe'
                                    END as group_code,
                                    CASE WHEN g.name is not null
                                    THEN g.name
                                    ELSE 'No existe'
                                    END as group_name
                                    FROM hr_holiday_book_employee h
                                    INNER JOIN hr_employee e ON e.id=h.employee_id
                                    INNER JOIN hr_contract c on c.id=h.contract_id
                                    LEFT JOIN logyca_budget_group g on g.id=e.budget_group_id
                                    WHERE h.active IS True 
                                    AND h.company_id=%s
                                    AND (c.date_end >= %s OR c.state=%s) and e.id in %s ''', 
                                        (self.company_id.id, self.date_to, 'open', tuple(self.employee_ids.ids)))
        else:
            self._cr.execute(''' SELECT 
                                    e.identification_id, 
                                    e.name, 
                                    to_char(c.date_start,'YYYY/MM/DD'),
                                    h.id,
                                    CASE WHEN g.code is not null
                                    THEN g.code
                                    ELSE 'No existe'
                                    END as group_code,
                                    CASE WHEN g.name is not null
                                    THEN g.name
                                    ELSE 'No existe'
                                    END as group_name
                                    FROM hr_holiday_book_employee h
                                    INNER JOIN hr_employee e ON e.id=h.employee_id
                                    INNER JOIN hr_contract c on c.id=h.contract_id
                                    LEFT JOIN logyca_budget_group g on g.id=e.budget_group_id
                                    WHERE h.active IS True 
                                    AND h.company_id=%s
                                    AND (c.date_end >= %s OR c.state=%s) ''', 
                                        (self.company_id.id, self.date_to, 'open'))
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
        ws.write(0, 0, 'REPORTE VACACIONES', title_head)
        ws.write(1, 0, str(self.company_id.name), title_head)
        ws.write(3, 0, 'Fecha Corte', title_head)
        ws.write(3, 1, str(self.date_to))
        ws.write(5, 0, 'Usuario', title_head)
        ws.write(5, 1, str(user.partner_id.name))
        ws.write(6, 0, 'Fecha Archivo', title_head)
        ws.write(6, 1, str(date_file))

        fila_title=9
        fila_title=9
        ws.write(fila_title, 0, 'Número Documento', subtitle_head)
        ws.write(fila_title, 1, 'Nombre Empleado', subtitle_head)
        ws.write(fila_title, 2, 'Fecha Ingreso', subtitle_head)        
        ws.write(fila_title, 3, 'Código Grupo presupuestal', subtitle_head)
        ws.write(fila_title, 4, 'Nombre Grupo presupuestal', subtitle_head)
        ws.write(fila_title, 5, 'Total Días', subtitle_head)
        ws.write(fila_title, 6, 'Días Tomados', subtitle_head)
        ws.write(fila_title, 7, 'Días Pendientes', subtitle_head)
        ws.write(fila_title, 8, 'Valor Proyectado', subtitle_head)

        fila=10
        for x in value:
            ws.write(fila,0,x[0],title_head)
            ws.write(fila,1,x[1],title_head)
            ws.write(fila,2,x[2],title_head)
            ws.write(fila,3,x[4],title_head)
            ws.write(fila,4,x[5],title_head)
            book_id = self.env['hr.holiday.book.employee'].search([('id', '=', x[3])], limit=1)
            holiday_pend, holiday_total, holiday_done = book_id.get_book_contract(book_id, self.date_to)
            amount = self.get_amount_holiday(book_id.contract_id, holiday_pend)
            ws.write(fila,5,holiday_total,title_head)
            ws.write(fila,6,holiday_done,title_head)
            ws.write(fila,7,holiday_pend,title_head)
            ws.write(fila,8,round(amount,2),title_head)
            fila+=1

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'ReporteVacaciones' + '-' + str(date_file)
        except ValueError:
            raise ValidationError('No se pudo generar el archivo')

    def get_amount_holiday(self, contract_id, total_days):
        return (contract_id.wage/30) * total_days