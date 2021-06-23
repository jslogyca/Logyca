# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRSubTypeJob(models.Model):
    _name = 'hr.sub.type.job'
    _description = 'Sub Type Job'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#