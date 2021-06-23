# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class TypeNoteEPayroll(models.Model):
    _name = 'type.note.epayroll'
    _description = 'Type Note EPayroll'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#