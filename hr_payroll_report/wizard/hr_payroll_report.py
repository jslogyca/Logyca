# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
import xlsxwriter
import requests


class HrPayrollReportLG(models.TransientModel):
    _name = 'hr.payroll.report.lg'
    _description = 'Hr Payroll Report LG'
  
    payslip_run_id  = fields.Many2one('hr.payslip.run', string='Payslip run', required=True)
    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")

    def do_report(self):
        value = self.get_values()
        if not value:
            raise Warning(_('!No hay resultados para los datos seleccionados¡'))
        self.make_file(value)

        if not self.data:
            raise UserError("No se generó el archivo correctamente.")

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=hr.payroll.report.lg&id={self.id}&field=data&filename_field=data_name&download=true",
            'target': 'self',
        }       
        
    def get_values(self):
        value = []
        # Busca asientos contables 
        if self.payslip_run_id:
            
            self._cr.execute(''' SELECT id, code, name FROM hr_salary_rule WHERE prenomina is True order by sequence_report''')
            rules_ids = self._cr.fetchall()
            
            query_header="select pr.name, \
                            em.identification_id, \
                            em.name, \
                            to_char(co.date_start,'YYYY/MM/DD'), \
                            jb.name, \
                            st.name, \
                            ct.acc_number, \
                            bk.name, \
                            co.wage"
            query_footer = ' from hr_payslip pa \
                            left join hr_payslip_run pr on (pr.id=pa.payslip_run_id) \
                            left join hr_employee em on (em.id=pa.employee_id) \
                            left join hr_contract co on (co.id=pa.contract_id) \
                            left join hr_job jb on (jb.id=em.job_id) \
                            left join hr_payroll_structure st on (st.id=pa.struct_id) \
                            left join res_partner_bank ct on (ct.id=em.bank_account_id) \
                            left join res_bank bk on (bk.id=ct.bank_id)'
            query_where=' where pa.payslip_run_id='+str(self.payslip_run_id.id)
            
            count=1
            query_rule=''
            query_left=''
            line_header='Procesamiento,ID,Nombre,Fecha de ingreso,Cargo,Estructura salarial,Cuenta bancaria,Banco,Salario'
            for rule in rules_ids:
                line_header += ',TOTAL ' + str(rule[2])
                query_rule += ', li' + str(count) + '.total'
                query_left += ' left join hr_payslip_line li' + str(count) + ' on (li' + str(count) + '.slip_id=pa.id and li' + str(count) + '.salary_rule_id=' + str(rule[0]) + ')'
                count+=1
            lines=[]
            lines.append(tuple(line_header.split(',')))
            self._cr.execute(query_header+query_rule+query_footer+query_left+query_where)
            lines+=self._cr.fetchall()
                
        return lines
    
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
        ws.write(0, 0, 'REPORTE GENERAL DE NOMINA', title_head)
        ws.write(1, 0, str(self.payslip_run_id.company_id.name), title_head)
        ws.write(2, 0, 'Procesamiento', title_head)
        ws.write(2, 1, str(self.payslip_run_id.name), title_head)
        ws.write(3, 0, 'Fecha Inicio', title_head)
        ws.write(3, 1, str(self.payslip_run_id.date_start), title_head)        
        ws.write(4, 0, 'Fecha Inicio', title_head)
        ws.write(4, 1, str(self.payslip_run_id.date_end), title_head)
        
        fila=6
        for x in value:
            if fila==6:
                ws.write_row(fila,0,x,subtitle_head)
            else:
                ws.write_row(fila,0,x)
            fila+=1
        try:
            wb.close()
            # out = base64.encodestring(buf.getvalue())
            out = base64.encodebytes(buf.getvalue())
            buf.close()
            self.data = out
            # self.data_name = unicode(str(self.payslip_run_id.name), 'utf-8')+".xlsx"
            self.data_name = str(self.payslip_run_id.name) + '-' + str(date_file)            
        except ValueError:
            raise Warning('No se pudo generar el archivo')

#