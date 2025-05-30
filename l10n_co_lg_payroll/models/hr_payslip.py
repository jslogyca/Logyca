# -*- coding: utf-8 -*-


from odoo import api, fields, models, tools, _
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict, Counter

from odoo.tools import float_round, date_utils, convert_file, html2plaintext

import logging
import random
import math
import pytz


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


    def action_refresh_from_work_entries(self):
        # Refresh the whole payslip in case the HR has modified some work entries
        # after the payslip generation
        if any(p.state not in ['draft', 'verify'] for p in self):
            raise UserError(_('The payslips should be in Draft or Waiting state.'))
        payslips = self.filtered(lambda p: not p.edited)
        payslips.mapped('worked_days_line_ids').unlink()
        payslips.mapped('line_ids').unlink()
        payslips._compute_worked_days_line_ids()
        payslips.update_input_employee()
        payslips.compute_sheet()

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        # delete old payslip lines
        payslips.line_ids.unlink()
        # this guarantees consistent results
        self.env.flush_all()
        today = fields.Date.today()
        for payslip in payslips:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            payslip.write({
                'number': number,
                'state': 'verify',
                'compute_date': today
            })
            payslip.update_input_employee()
        self.env['hr.payslip.line'].create(payslips._get_payslip_lines())
        return True

    def update_input_employee(self):
        for payslip in self:
            if not payslip.contract_id:
                payslip.struct_id = False
            payslip.with_context(contract=True)._get_new_input_line_ids()
            payslip.with_context(contract=True)._compute_worked_days_line_ids()
        return

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        if not self or self.env.context.get('salary_simulation'):
            return
        valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
        if not valid_slips:
            return
        # Make sure to reset invalid payslip's worked days line
        self.update({'worked_days_line_ids': [(5, 0, 0)]})
        # Ensure work entries are generated for all contracts
        generate_from = min(p.date_from for p in valid_slips) + relativedelta(days=-1)
        generate_to = max(p.date_to for p in valid_slips) + relativedelta(days=1)
        self.contract_id.generate_work_entries(generate_from, generate_to)

        work_entries = self.env['hr.work.entry'].search([
            ('date_stop', '<=', generate_to),
            ('date_start', '>=', generate_from),
            ('contract_id', 'in', self.contract_id.ids),
        ])
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            work_entries_by_contract[work_entry.contract_id.id] += work_entry

        for slip in valid_slips:
            if not slip.struct_id.use_worked_day_lines:
                continue

            # convert slip.date_to to a datetime with max time to compare correctly in filtered_domain.
            slip_tz = pytz.timezone(slip.contract_id.resource_calendar_id.tz)
            utc = pytz.timezone('UTC')
            date_from = slip_tz.localize(datetime.combine(slip.date_from, time.min)).astimezone(utc).replace(tzinfo=None)
            date_to = slip_tz.localize(datetime.combine(slip.date_to, time.max)).astimezone(utc).replace(tzinfo=None)
            payslip_work_entries = work_entries_by_contract[slip.contract_id].filtered_domain([
                ('date_stop', '<=', date_to),
                ('date_start', '>=', date_from),
            ])
            payslip_work_entries._check_undefined_slots(slip.date_from, slip.date_to)
            # YTI Note: We can't use a batched create here as the payslip may not exist
            slip.update({'worked_days_line_ids': slip._get_new_worked_days_lines()})

    # @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    # def _compute_worked_days_line_ids(self):
    #     if self.env.context.get('salary_simulation') or any(not p.date_to or not p.date_from for p in self):
    #         return
    #     valid_slips = self.filtered(lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
    #     # Make sure to reset invalid payslip's worked days line
    #     invalid_slips = self - valid_slips
    #     invalid_slips.worked_days_line_ids = [(5, False, False)]
    #     if not valid_slips:
    #         return
    #     # Ensure work entries are generated for all contracts
    #     generate_from = min(p.date_from for p in self)
    #     current_month_end = date_utils.end_of(fields.Date.today(), 'month')
    #     generate_to = max(min(fields.Date.to_date(p.date_to), current_month_end) for p in valid_slips)
    #     self.mapped('contract_id')._generate_work_entries(generate_from, generate_to)

    #     for slip in valid_slips:
    #         slip.mapped('worked_days_line_ids').unlink()
    #         if slip._origin.id:
    #             slip_number = slip._origin.id
    #         else:
    #             slip_number = slip.id
    #             continue

    #         for vals in slip._get_worked_day_lines():
    #             self.env["hr.payslip.worked_days"].create(
    #                 {
    #                     "sequence": vals["sequence"],
    #                     "work_entry_type_id": vals["work_entry_type_id"],
    #                     "number_of_days": vals["number_of_days"],
    #                     "number_of_hours": vals["number_of_hours"],
    #                     "payslip_id": slip_number,
    #                 }
    #             )
    #             slip.with_context(contract=True)._get_new_input_line_ids()
    #             self.env.cr.commit()

    # def _get_worked_day_lines_values(self, domain=None):
    #     self.ensure_one()
    #     res = []
    #     hours_per_day = self._get_worked_day_lines_hours_per_day()
    #     work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
    #     work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
    #     biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
    #     add_days_rounding = 0
    #     for work_entry_type_id, hours in work_hours_ordered:
    #         work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
    #         days = round(hours / hours_per_day, 5) if hours_per_day else 0
    #         if work_entry_type_id == biggest_work:
    #             days += add_days_rounding
    #         day_rounded = self._round_days(work_entry_type, days)
    #         add_days_rounding += (days - day_rounded)
    #         attendance_line = {
    #             'sequence': work_entry_type.sequence,
    #             'work_entry_type_id': work_entry_type_id,
    #             'number_of_days': day_rounded,
    #             'number_of_hours': hours,
    #         }
    #         res.append(attendance_line)
    #     return res

    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id.get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            attendance_line = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)

        # Sort by Work Entry Type sequence
        work_entry_type = self.env['hr.work.entry.type']
        return sorted(res, key=lambda d: work_entry_type.browse(d['work_entry_type_id']).sequence)
     

    def action_payslip_cancel_done(self):
        if self.filtered(lambda slip: slip.state == "done"):
            self.move_id.button_draft()
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
        # else:
        #     self.env.cr.execute(
        #         """
        #             SELECT c.wage*5
        #             FROM hr_payslip_line l
        #             INNER JOIN hr_payslip n on n.id=l.slip_id
        #             INNER JOIN hr_employee e on e.id=n.employee_id
        #             INNER JOIN hr_contract c on c.id=n.contract_id
        #             INNER JOIN hr_salary_rule r on r.id=l.salary_rule_id
        #             WHERE r.base_prima = 'base_salary'
        #             AND n.employee_id=%s and n.state='done'
        #             and n.date_from BETWEEN %s and %s limit 1 """, (self.employee_id.id, from_date, to_date),
        #     )            
        res = self.env.cr.fetchone()
        return res and res[0] or 0.0

    def _get_lines_aux_transp_prima(self, from_date, to_date):
        self.ensure_one()
        if self.contract_id.aux_transp_full:
            self.env.cr.execute(
                """
                    SELECT amount_fix*5
                    FROM hr_salary_rule
                    WHERE code=%s """,('F_AUXTRANSPVALOR',)
            )
        else:
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

