# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HRReasonEndContract(models.Model):
    _name = 'hr.reason.end.contract'
    _description = "Reason End Contract"
    _order = "name desc"

    name = fields.Char('Name')
    code = fields.Char('Code')


