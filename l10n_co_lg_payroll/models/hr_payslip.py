# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta


def days_between(start_date, end_date):
    #Add 1 day to end date to solve different last days of month 
    #s1, e1 =  datetime.strptime(start_date,"%Y-%m-%d") , datetime.strptime(end_date,"%Y-%m-%d")  + timedelta(days=1)
    s1, e1 =  start_date , end_date + timedelta(days=1)
    #Convert to 360 days
    s360 = (s1.year * 12 + s1.month) * 30 + s1.day
    e360 = (e1.year * 12 + e1.month) * 30 + e1.day
    #Count days between the two 360 dates and return tuple (months, days)
    res = divmod(e360 - s360, 30)
    return ((res[0] * 30) + res[1]) or 0

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    payroll_liquid = fields.Boolean(related='struct_id.payroll_liquid')
    reason_id= fields.Many2one('hr.reason.end.contract', string='Reason')
    general_line_ids = fields.One2many('hr.payslip.line', 'slip_id', string="Payslip Lines", readonly=True,
        domain=[('appears_on_payslip', '=', True),('total','!=',0.0)],
        states={"draft": [("readonly", False)]},
    )

    def update_input_employee(self):
        if not self.contract_id:
            self.struct_id = False
        self.with_context(contract=True)._get_new_input_line_ids()
        self.with_context(contract=True)._onchange_worked_days_inputs()
        return

    def action_payslip_cancel_done(self):
        if self.filtered(lambda slip: slip.state == "done"):
            self.move_id.button_draft()
            # self.move_id.unlink()
        return self.write({"state": "cancel"})

    def get_change_salary(self, employee_id, from_date, to_date):
        self.env.cr.execute(
            """
                SELECT l.total
                FROM hr_payslip_line l
                INNER JOIN hr_payslip n on n.id=l.slip_id
                INNER JOIN hr_employee e on e.id=n.employee_id
                INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
                WHERE r.base_prima = 'base_salary'
                AND n.employee_id=%s and n.state='done'
                and n.date_from BETWEEN %s and %s 
                order by n.date_from desc """, (employee_id.id, from_date, to_date),
        )
        salary_ids = self.env.cr.fetchone()
        if salary_ids:
            month = 0
            salary = 0
            for salary_id in salary_ids:
                if month <= 3:
                    if salary == 0 or salary == salary_id:
                        salary = salary_id
                        prom_salary = False
                        continue
                    else:
                        prom_salary = True
        return prom_salary

    @api.model
    def _get_new_input_line_ids(self):
        if self.struct_id and self.struct_id.input_line_type_ids:
            # computation of the salary worked days
            input_line_id_values = self._get_input_line()
            input_lines_id = self.input_line_ids.browse([])
            for r in input_line_id_values:
                input_lines_id |= input_lines_id.new(r)
            if input_lines_id:
                self.update({'input_line_ids': input_lines_id})       

    def _get_input_line(self):
        res = []
        for input_lines in self.struct_id.input_line_type_ids:
            input_line = {
                'sequence': input_lines.sequence,
                'input_type_id': input_lines.id,
                'amount': 0.0,
            }
            res.append(input_line)
        return res

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'average_salary_prima': average_salary_prima,
            'aux_transp_prima': aux_transp_prima,
            'variable_salary_prima': variable_salary_prima,
            'days_leave_prima': days_leave_prima,
        })
        return res

    def _get_lines_base_salayr_prima(self, from_date, to_date):
        self.ensure_one()
        if self.get_change_salary(self.employee_id, from_date, to_date):
            self.env.cr.execute(
                """
                    SELECT coalesce(SUM(l.total),0.0)
                    FROM hr_payslip_line l
                    INNER JOIN hr_payslip n on n.id=l.slip_id
                    INNER JOIN hr_employee e on e.id=n.employee_id
                    INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
                    WHERE r.base_prima = 'base_salary'
                    AND n.employee_id=%s and n.state='done'
                    and n.date_from BETWEEN %s and %s """, (self.employee_id.id, from_date, to_date),
            )
        else:
            self.env.cr.execute(
                """
                    SELECT c.wage*5
                    FROM hr_payslip_line l
                    INNER JOIN hr_payslip n on n.id=l.slip_id
                    INNER JOIN hr_employee e on e.id=n.employee_id
                    INNER JOIN hr_contract c on c.id=n.contract_id
                    INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
                    WHERE r.base_prima = 'base_salary'
                    AND n.employee_id=%s and n.state='done'
                    and n.date_from BETWEEN %s and %s limit 1 """, (self.employee_id.id, from_date, to_date),
            )            
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _get_lines_aux_transp_prima(self, from_date, to_date):
        self.ensure_one()
        self.env.cr.execute(
            """
                SELECT coalesce(SUM(l.total),0.0)
                FROM hr_payslip_line l
                INNER JOIN hr_payslip n on n.id=l.slip_id
                INNER JOIN hr_employee e on e.id=n.employee_id
                INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
                WHERE r.aux_transp IS True
                AND n.employee_id=%s and n.state='done'
                and n.date_from BETWEEN %s and %s """, (self.employee_id.id, from_date, to_date),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _get_lines_variable_prima(self, from_date, to_date):
        self.ensure_one()
        self.env.cr.execute(
            """
                SELECT coalesce(SUM(l.total),0.0)
                FROM hr_payslip_line l
                INNER JOIN hr_payslip n on n.id=l.slip_id
                INNER JOIN hr_employee e on e.id=n.employee_id
                INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
                WHERE r.base_prima = 'variable_salary'
                AND n.employee_id=%s and n.state='done'
                and n.date_from BETWEEN %s and %s """, (self.employee_id.id, from_date, to_date),
        )
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _get_days_leave_prima(self, from_date, to_date):
        self.ensure_one()
        if to_date is None:
            to_date = fields.Date.today()
        days_period = 0.0
        day_to = datetime.strptime(from_date,"%Y-%m-%d")
        if str(self.contract_id.date_start) > from_date:
            days_period = (days_between(day_to, self.contract_id.date_start))-1
        self.env.cr.execute(
            """
                SELECT coalesce(sum(number_of_days),'0.0')
                FROM hr_leave h
                INNER JOIN hr_leave_type t on t.id=h.holiday_status_id
                WHERE employee_id=%s AND date_from between %s AND %s
                AND leave_prima is True""", (self.employee_id.id, from_date, to_date),
        )
        res = self.env.cr.fetchone()
        return res and res[0]+days_period or 0.0

def average_salary_prima(payslip, categories, worked_days, inputs, from_date, to_date):
    base_prima = payslip.dict._get_lines_base_salayr_prima(from_date, to_date)
    return base_prima

def aux_transp_prima(payslip, categories, worked_days, inputs, from_date, to_date):
    base_prima = payslip.dict._get_lines_aux_transp_prima(from_date, to_date)
    return base_prima

def variable_salary_prima(payslip, categories, worked_days, inputs, from_date, to_date):
    base_prima = payslip.dict._get_lines_variable_prima(from_date, to_date)
    return base_prima

def days_leave_prima(payslip, categories, worked_days, inputs, from_date, to_date):
    days_leave = payslip.dict._get_days_leave_prima(from_date, to_date)
    return days_leave
