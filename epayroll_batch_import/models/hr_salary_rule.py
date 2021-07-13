# -*- coding:utf-8 -*-

from odoo import api, fields, models, _

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    
    x_reference = fields.Char(string='Reference')
