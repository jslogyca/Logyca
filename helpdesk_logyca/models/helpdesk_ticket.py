# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.depends('vinculation', 'x_type_vinculation', 'company_id')
    def _get_vinculation(self):
        for help in self:
            if help.partner_id:
                if help.partner_id.parent_id:
                    miembro = False
                    if help.partner_id.parent_id.x_type_vinculation:
                        for vinculation_id in help.partner_id.parent_id.x_type_vinculation:
                            if miembro:
                                continue
                            help.x_type_vinculation = vinculation_id.id
                            if vinculation_id.id == 1:
                                miembro = True
                        help.vinculation = True
                    else:
                        help.x_type_vinculation = 12
                        help.vinculation = True
                else:
                    if help.partner_id.x_type_vinculation:
                        miembro = False
                        for vinculation_id in help.partner_id.x_type_vinculation:
                            if miembro:
                                continue
                            help.x_type_vinculation = vinculation_id.id
                            if vinculation_id.id == 1:
                                miembro = True
                        help.vinculation = True
                    else:
                        help.x_type_vinculation = 12
                        help.vinculation = True
            else:
                help.vinculation = True

    vat_partner = fields.Char(related='partner_id.vat')
    station_id = fields.Many2one('helpdesk.station', string='Station')
    colabor_id = fields.Many2one('res.partner', string='Colaborator')
    ticket_interno = fields.Boolean(related='team_id.ticket_interno')
    service_id = fields.Many2one('helpdesk.service', string='Service')
    platform_id = fields.Many2one('helpdesk.platform', string='Platform')
    subtype_id = fields.Many2one('helpdesk.ticket.sub.type', string='Sub Type')
    type_desk = fields.Selection([("pqrs","PQRSF (Peticiones, Quejas, Reclamo, Solucitudes y Felicitaciones)"),
                                    ("support","Support"),
                                    ("sale","Sale")], string='Desk Type', default='support')    
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    vinculation = fields.Boolean(compute='_get_vinculation', string='Vinculation')

    def _get_vinculation_by_ticket(self, ticket):
        if ticket:
            if ticket.partner_id:
                if ticket.partner_id.parent_id:
                    miembro = False
                    if ticket.partner_id.parent_id.x_type_vinculation:
                        for vinculation_id in ticket.partner_id.parent_id.x_type_vinculation:
                            if miembro:
                                continue
                            ticket.write({'x_type_vinculation': vinculation_id.id})
                            if vinculation_id.id == 1:
                                miembro = True                            
                        ticket.write({'vinculation': True})
                    else:
                        ticket.write({'x_type_vinculation': 12})
                        ticket.write({'vinculation': True})
                else:                
                    if ticket.partner_id.x_type_vinculation:
                        miembro = False
                        for vinculation_id in ticket.partner_id.x_type_vinculation:
                            if miembro:
                                continue                            
                            ticket.write({'x_type_vinculation': vinculation_id.id})
                            if vinculation_id.id == 1:
                                miembro = True                            
                        ticket.write({'vinculation': True})
                    else:
                        ticket.write({'x_type_vinculation': 12})
                        ticket.write({'vinculation': True})
            else:
                ticket.write({'vinculation': True})
