# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRContractEType(models.Model):
    _name = 'hr.contract.etype'
    _description = 'HR Contract EType'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#