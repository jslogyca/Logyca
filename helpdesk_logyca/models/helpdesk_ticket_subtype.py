# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTicketSubType(models.Model):
    _name = 'helpdesk.ticket.sub.type'
    _description = 'Helpdesk Ticket Sub Type'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active')
