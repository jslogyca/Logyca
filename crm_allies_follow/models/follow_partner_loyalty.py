# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FollowPartnerLoyalty(models.Model):
    _name = 'follow.partner.loyalty'
    _description = 'Follow Partner Loyalty'

    name = fields.Char('Name')
    date = fields.Date(string='Fecha de Fidelización', default=fields.Date.context_today)
    description = fields.Text('Obsercaciones')
    contact_partner = fields.Char('Nombre Contacto')
    job_partner = fields.Char('Cargo')
    phone_partner = fields.Char('Teléfono')
    email_partner = fields.Char('Correo Electrónico')
    partner_id = fields.Many2one('res.partner', string="Partner", domain = [('parent_id', '=', False)])
    check_loyalty = fields.Boolean(string='Vinculation', default=False, compute='_get_check_loyalty',)

    def name_get(self):
        return [(follow.id, '%s - %s' %
                 (follow.partner_id.name, follow.date)) for follow in self]

    @api.depends('partner_id', 'description')
    def _get_check_loyalty(self):
        for move in self:
            if move.partner_id:
                move.check_loyalty = True
                move.partner_id.date_loyalty = move.date
                move.partner_id.meet_loyalty = 'SI'
                move.partner_id.description_loyalty = move.description
            else:
                move.check_loyalty = True
          
