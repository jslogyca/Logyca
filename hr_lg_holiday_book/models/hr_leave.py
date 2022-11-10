# -*- coding: utf-8 -*-

from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools, _

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

class HRLeave(models.Model):
    _inherit = "hr.leave"

    @api.depends('date_from', 'date_to', 'employee_id')
    def _compute_number_of_days_calendar(self):
        for holiday in self:
            if holiday.date_from and holiday.date_to:
                holiday.number_of_days_calendar = days_between(holiday.date_from, holiday.date_to)
            else:
                holiday.number_of_days_calendar = 0

    contract_id = fields.Many2one('hr.contract', string='Contract')
    number_of_days_calendar = fields.Float(
        'Duration (Days)', compute='_compute_number_of_days_calendar', store=True, readonly=False, copy=False, tracking=True,
        help='Number of days of the time off request. Used in the calculation. To manually correct the duration, use this field.')    

    @api.model
    def create(self, vals):
        if vals.get('employee_id', False) or vals.get('holiday_status_id', False):
            contract_id = self.env['hr.contract'].search([('employee_id', '=', vals.get('employee_id', False)), ('state', '=', 'open')], limit=1)
            if contract_id:
                vals['contract_id']= contract_id.id
        res = super(HRLeave, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('employee_id', False) or vals.get('holiday_status_id', False):
            contract_id = self.env['hr.contract'].search([('employee_id', '=', vals.get('employee_id', False)), ('state', '=', 'open')], limit=1)
            if contract_id:
                vals['contract_id']= contract_id.id
        res = super(HRLeave, self).write(vals)
        return res

    @api.onchange('company_id', 'employee_id')
    def _onchange_contract_id(self):
        if self.employee_id and self.id:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
            if contract_id:
                self.write({'contract_id': contract_id})
            else:
                raise UserError(_("The employee %s is not contract active") % self.employee_id.name)    
