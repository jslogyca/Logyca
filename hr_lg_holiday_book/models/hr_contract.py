# -*- coding: utf-8 -*-

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _

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

class HRContract(models.Model):
    _inherit = "hr.contract"

    def _compute_holiday_book(self):
        self.holiday_book_count = len(self.holiday_book_id)    

    holiday_book_count = fields.Integer(string="Holiday Book Count", compute='_compute_holiday_book')
    holiday_book_id = fields.Many2one('hr.holiday.book.employee', string='Holiday Book')

    def calcula_holidays_done(self, contract_id):
        if contract_id:
            leave_ids = self.env['hr.leave'].search([('contract_id', '=', contract_id.id), ('state', '=', 'validate')])
            total=0.0
            for leave_id in leave_ids:
                total+=leave_id.number_of_days
            return total

    def create_book_holidays(self, day_to, company_id):
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open'),('holiday_book_id', '=', None),('company_id', '=', company_id)], order="id desc")
        day_to = fields.Datetime.now()
        if contract_ids:
            holiday_total = 0.0
            holiday_done = 0.0
            holiday_pend = 0.0            
            for contract_id in contract_ids:
                holiday_total = days_between(contract_id.date_start, day_to)
                holiday_done = self.calcula_holidays_done(contract_id)
                holiday_pend = holiday_total - holiday_done                
                book_id = self.env['hr.holiday.book.employee'].create({'name': str(contract_id.employee_id.name),
                                            'holiday_pending': holiday_pend,
                                            'holiday_done': holiday_done,
                                            'employee_id': contract_id.employee_id.id,
                                            'contract_id': contract_id.id,
                                            'company_id': company_id,
                                        })
                self.env.cr.commit()
                contract_id.write({'holiday_book_id': book_id.id})
                self.env.cr.commit()

    def create_book_holidays_byid(self, day_to, contract):
        contract_ids = self.env['hr.contract'].search([('state', '=', 'open'),('id', '=', contract), ('holiday_book_id', '=', None)], order="id desc")
        day_to = fields.Datetime.now()
        if contract_ids:
            holiday_total = 0.0
            holiday_done = 0.0
            holiday_pend = 0.0            
            for contract_id in contract_ids:
                holiday_total = days_between(contract_id.date_start, day_to)
                holiday_done = self.calcula_holidays_done(contract_id)
                holiday_pend = holiday_total - holiday_done                
                book_id = self.env['hr.holiday.book.employee'].create({'name': str(contract_id.employee_id.name),
                                            'holiday_pending': holiday_pend,
                                            'holiday_done': holiday_done,
                                            'employee_id': contract_id.employee_id.id,
                                            'contract_id': contract_id.id,
                                            'company_id': contract_id.company_id.id,
                                        })
                self.env.cr.commit()
                contract_id.write({'holiday_book_id': book_id.id})
                self.env.cr.commit()
