# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    book_holiday = fields.Selection([('holiday', 'Holiday'),
                                ('holiday_pay', 'Holiday Pay'),
                                ('other_holiday', 'Holiday Other'),
                                ('na_holidays', 'Not Holiday'),
                                ('na', 'No Apply')], string='Book Holiday', default='na')
