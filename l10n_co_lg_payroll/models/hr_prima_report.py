# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HRPrimaReport(models.Model):
    _name = 'hr.prima.report'
    _description = "Prima Report"
    _auto = False
    _order = "id asc"

    id = fields.Integer('ID')
    payslip_id = fields.Many2one('hr.payslip', string='Payslip')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    structure_id = fields.Many2one('hr.payroll.structure', string='Structure')
    payslip_run_id = fields.Many2one('hr.payslip.run', string='Slip Run')
    identification_id = fields.Char('Identification')
    date_init = fields.Date('Date Init')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To Prima')
    total_days = fields.Float('Total días')
    total_leave_days = fields.Float('Días Ausencias')
    total_days_prima = fields.Float('Total días Prima')
    salary_now = fields.Float('Salario Actual')
    salary_prom = fields.Float('Prom. Salario')
    salary_var_prom = fields.Float('Prom. Salario Variable')
    aux_transp_prom = fields.Float('Prom Aux Transpo')
    base_prima = fields.Float('Base Prima')
    prima = fields.Float('Prima')    

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))         

    def _select(self):
        select_str = """
        SELECT
            n.id as payslip_id,
            n.id as id,
            c.date_start as date_init,
            n.date_from as date_from,
            n.date_from as date_to,
            e.id as employee_id,
            n.struct_id as structure_id,
            n.payslip_run_id as payslip_run_id,
            e.identification_id as identification_id,
            (SELECT total FROM hr_payslip_line WHERE code='F_TOTALDIASPRIMA' and slip_id=n.id limit 1) as total_days,
            (SELECT total FROM hr_payslip_line WHERE code='TOTALDIASAUSENCIAPRIMA' and slip_id=n.id limit 1) as total_leave_days,
            (SELECT total FROM hr_payslip_line WHERE code='DIASPAGADOSPRIMA' and slip_id=n.id limit 1) as total_days_prima,
            c.wage as salary_now,
            (SELECT total FROM hr_payslip_line WHERE code='PROMEDIOSALARIOPRIMA' and slip_id=n.id limit 1) as salary_prom,
            (SELECT total FROM hr_payslip_line WHERE code='PROMVARIAPRIMA' and slip_id=n.id limit 1) as salary_var_prom,
            (SELECT total FROM hr_payslip_line WHERE code='PROMEDIOAUXTRANSPOPRIMA' and slip_id=n.id limit 1) as aux_transp_prom,
            (SELECT total FROM hr_payslip_line WHERE code='BASEPRIMAPROYECTADA' and slip_id=n.id limit 1) as base_prima,
            l.total as prima
		"""
        return select_str

    def _from(self):
        from_str = """
            hr_payslip_line l
                INNER JOIN hr_payslip n on n.id=l.slip_id
                INNER JOIN hr_employee e on e.id=n.employee_id
                INNER JOIN hr_contract c on c.id=n.contract_id
        """
        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE l.code in ('PRIMA') and l.total > 0.0
                ORDER BY n.id DESC
        """
        return group_by_str

