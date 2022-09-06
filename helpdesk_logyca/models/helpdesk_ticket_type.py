# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTicketType(models.Model):
    _inherit = 'helpdesk.ticket.type'

    active = fields.Boolean('Active', default=True)
    service_id = fields.Many2one('helpdesk.service', string='Service')
