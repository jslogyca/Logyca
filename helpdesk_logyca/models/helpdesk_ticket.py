# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    vat_partner = fields.Char(related='partner_id.vat')
    station_id = fields.Many2one('helpdesk.station', string='Station')
    colabor_id = fields.Many2one('res.partner', string='Colaborator')
    ticket_interno = fields.Boolean(related='team_id.ticket_interno')
    service_id = fields.Many2one('helpdesk.service', string='Service')
    subtype_id = fields.Many2one('helpdesk.ticket.sub.type', string='Sub Type')
