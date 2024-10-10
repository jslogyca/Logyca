# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRETypeLeave(models.Model):
    _name = 'hr.etype.leave'
    _description = 'HR EType Leave'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
