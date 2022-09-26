# -*- coding: utf-8 -*-

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HRHolidayBookAjust(models.Model):
    _name = 'hr.holiday.book.ajust'
    _description = "Holiday Book Ajust"
    _order = "date asc"

    name = fields.Char('Name')
    days_ajust = fields.Float('Holidays Ajust', default=0.0)
    date = fields.Date('Date')
    book_id = fields.Many2one('hr.holiday.book.employee', string='Book')
