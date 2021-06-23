# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRTypeEJob(models.Model):
    _name = 'hr.type.ejob'
    _description = 'HR Type EJob'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#