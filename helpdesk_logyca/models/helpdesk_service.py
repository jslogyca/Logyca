# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskService(models.Model):
    _name = 'helpdesk.service'
    _description = 'Helpdesk Service'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')
