# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    
    email_payroll = fields.Char(string="Payroll Email", groups="hr.group_hr_user")
