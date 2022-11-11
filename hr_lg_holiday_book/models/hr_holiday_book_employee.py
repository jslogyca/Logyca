# -*- coding: utf-8 -*-

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

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

class HRHolidayBookEmployee(models.Model):
    _name = 'hr.holiday.book.employee'
    _description = "Holiday Book Employee"
    _inherit = ['mail.thread']
    _order = "id asc"

    def _compute_holidays_done(self):
        for book in self:
            leave_ids = self.env['hr.leave'].search([('contract_id', '=', book.contract_id.id), ('state', '=', 'validate'),
                                                                    ('holiday_status_id.book_holiday', 'in', ('holiday', 'holiday_pay'))])
            book.leave_done_ids = leave_ids

    def _compute_holidays_na(self):
        for book in self:
            leave_ids = self.env['hr.leave'].search([('contract_id', '=', book.contract_id.id), ('state', '=', 'validate'),
                                                                    ('holiday_status_id.book_holiday', '=', 'na_holidays')])
            book.leave_na_ids = leave_ids

    name = fields.Char('Name')
    holiday_pending = fields.Float('Holidays Pending', default=0.0)
    holiday_done = fields.Float('Holidays Done', default=0.0)
    holiday_total = fields.Float('Total', default=0.0)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr.contract', string='Contract')
    leave_done_ids = fields.One2many('hr.leave', compute="_compute_holidays_done", string="Holidays Done", tracking=True)
    leave_na_ids = fields.One2many('hr.leave', compute="_compute_holidays_na", string="Holidays Na", tracking=True)
    active = fields.Boolean('Active', default=True)
    date_start = fields.Date(related='contract_id.date_start')
    date_end = fields.Date(related='contract_id.date_end')
    leave_ajust_ids = fields.One2many('hr.holiday.book.ajust', 'book_id', string="Holidays Ajust", tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)    

    def calcula_holidays_ajust(self, book_id):
        if book_id:
            total=0.0
            for leave in book_id.leave_ajust_ids:
                total+=leave.days_ajust
            return total

    def calcula_holidays_done(self, book_id):
        if book_id:
            total=0.0
            for leave in book_id.leave_done_ids:
                if leave.holiday_status_id.book_holiday == 'holiday':
                    total+=leave.number_of_days
                if leave.holiday_status_id.book_holiday in ('holiday_pay', 'other_holiday'):
                    total+=leave.number_of_days_calendar
            return total

    def calcula_holidays_done_bydate(self, book_id, date):
        if book_id:
            total=0.0
            for leave in book_id.leave_done_ids:
                if leave.holiday_status_id.book_holiday == 'holiday' and leave.request_date_from<=date:
                    total+=leave.number_of_days
                if leave.holiday_status_id.book_holiday in ('holiday_pay', 'other_holiday') and leave.request_date_from<=date:
                    total+=leave.number_of_days_calendar
            return total

    def calcula_holidays_na(self, book_id):
        if book_id:
            total=0.0
            for leave in book_id.leave_na_ids:
                if leave.holiday_status_id.book_holiday == 'na_holidays':
                    total+=leave.number_of_days_calendar
            return total

    def update_book_holidays(self, day_to):
        book_ids = self.env['hr.holiday.book.employee'].search([('active', '=', True)], order="id desc")
        print('boooks', book_ids)
        day_to = fields.Datetime.now()
        date_start = fields.Datetime.now().date()
        date_start = date_start.replace(day=1)
        date_start = date_start.replace(month=1)
        date_start = date_start.replace(year=2022)
        if book_ids:
            holiday_total = 0.0
            holiday_done = 0.0
            holiday_pend = 0.0
            holiday_na = 0.0
            holiday_ajust = 0.0
            for book_id in book_ids:
                if book_id.contract_id.date_start > date_start:
                    date_start = book_id.contract_id.date_start
                holiday_na = self.calcula_holidays_na(book_id)
                holiday_ajust = self.calcula_holidays_ajust(book_id)
                holiday_total = ((days_between(date_start, day_to)-holiday_na)*15)/360
                holiday_total = holiday_total + holiday_ajust
                holiday_done = self.calcula_holidays_done(book_id)
                holiday_pend = holiday_total - holiday_done                
                book_id.write({'holiday_pending': holiday_pend, 'holiday_done':holiday_done, 'holiday_total': holiday_total})
                self.env.cr.commit()
        return

    def get_book_contract(self, book_id, date_to):
        day_to = date_to
        date_start = fields.Datetime.now().date()
        date_start = date_start.replace(day=1)
        date_start = date_start.replace(month=1)
        date_start = date_start.replace(year=2022)
        if book_id:
            holiday_total = 0.0
            holiday_done = 0.0
            holiday_pend = 0.0
            holiday_na = 0.0
            holiday_ajust = 0.0
            for book_id in book_id:
                if book_id.contract_id.date_start > date_start:
                    date_start = book_id.contract_id.date_start
                holiday_na = self.calcula_holidays_na(book_id)
                holiday_ajust = self.calcula_holidays_ajust(book_id)
                holiday_total = ((days_between(date_start, day_to)-holiday_na)*15)/360
                holiday_total = holiday_total + holiday_ajust
                holiday_done = self.calcula_holidays_done_bydate(book_id, date_to)
                holiday_pend = holiday_total - holiday_done
        return round(holiday_pend,2), round(holiday_total,2), round(holiday_done,2)

    def update_book_holidays_byid(self):
        day_to = fields.Datetime.now()
        date_start = fields.Datetime.now().date()
        date_start = date_start.replace(day=1)
        date_start = date_start.replace(month=1)
        date_start = date_start.replace(year=2022)
        holiday_total = 0.0 
        holiday_done = 0.0
        holiday_pend = 0.0
        holiday_na = 0.0
        holiday_ajust = 0.0
        for book_id in self:
            if book_id.contract_id.date_start > date_start:
                date_start = book_id.contract_id.date_start
            holiday_na = self.calcula_holidays_na(book_id)
            holiday_ajust = self.calcula_holidays_ajust(book_id)
            holiday_total = ((days_between(date_start, day_to)-holiday_na)*15)/360
            holiday_total = holiday_total + holiday_ajust
            holiday_done = self.calcula_holidays_done(book_id)
            holiday_pend = holiday_total - holiday_done
            book_id.write({'holiday_pending': holiday_pend, 'holiday_done':holiday_done, 'holiday_total': holiday_total})
            self.env.cr.commit()
        return
