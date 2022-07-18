# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskStation(models.Model):
    _name = 'helpdesk.station'
    _description = 'Helpdesk Station'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')
