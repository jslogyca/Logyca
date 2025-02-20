# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class LogycaMemberRed(models.Model):
    _name = 'logyca.member.red'
    _description = 'Logyca Member Red'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)

    def name_get(self):
        return [(reason.id, '%s' %
                 (reason.name)) for reason in self]
