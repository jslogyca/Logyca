# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskPlatform(models.Model):
    _name = 'helpdesk.platform'
    _description = 'Helpdesk Platform'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)
