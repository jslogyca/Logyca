# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEPayslipsEmployees(models.TransientModel):
    _name = 'hr.epayslips.by.employees'
    _description = 'Generate epayslips for all selected employees'

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_epayslip_rel', 'epayslip_id', 'employee_id', 'Employees')

    def compute_sheet_epayslip(self):
        epayslips = self.env['epayslip.bach']
        employee_inv = []
        employee_all = []
        [data] = self.read()
        active_id = self.env.context.get('active_id')
        if active_id:
            [run_data] = self.env['epayslip.bach.run'].browse(active_id).read(['start_date', 'finish_date', 'type_epayroll'])
        from_date = run_data.get('start_date')
        to_date = run_data.get('finish_date')
        type_document = run_data.get('type_epayroll')[0]
        name='NOMINA ELECTRONICA'
        self._cr.execute(''' SELECT employee_id FROM epayslip_bach WHERE epayslip_bach_run_id=%s ''', (run_data.get('id'),))
        employees_inv = self._cr.fetchall()
        for emp in employees_inv:
            employee_inv.append(emp[0])
        self._cr.execute(''' SELECT count(*), employee_id
                                FROM hr_payslip
                                WHERE date_from >= %s and date_to <= %s
                                AND state = 'done'
                                GROUP BY employee_id ''', (from_date, to_date))
        employees_payslip = self._cr.fetchall()
        for e_payslip in employees_payslip:
            employee_all.append(e_payslip[1])
        if not employee_all:
            raise ValidationError('No existen nóminas en el periodo')
        # for employee in self.env['hr.employee'].browse(data['employee_ids']):
        for employee in self.env['hr.employee'].search([('id', 'in', employee_all), ('id', 'not in', employee_inv)]):
            contract_id = self.env['hr.contract'].search([('employee_id','=',employee.id)], limit=1)
            print('CONTRATO ///', contract_id, employee)
            if not contract_id:
                raise ValidationError('No existe un contrato!')
        #     slip_data = self.env['hr.payslip'].onchange_employee_id(from_date, to_date, employee.id, contract_id=False)
            res = {
                'employee_id': employee.id,
                'contract_id': contract_id.id,
                'name': name,
                'epayslip_bach_run_id': active_id,
                # 'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids')],
                # 'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids')],
                'start_date': from_date,
                'finish_date': to_date,
                'company_id': employee.company_id.id,
                'type_epayroll': type_document,
            }
            epayslips = self.env['epayslip.bach'].create(res)
            # epayslips.action_generated()
            self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}
