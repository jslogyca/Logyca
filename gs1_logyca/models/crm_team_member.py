# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CrmTeamMember(models.Model):
    _inherit = 'crm.team.member'

    total_amount = fields.Float(string='Meta de Facturación', default=0.00)
    total_invoice = fields.Float(string='Total Facturado', default=0.00)
    total_amount_team = fields.Float(string='Meta de Facturación Equipo', related='crm_team_id.total_amount')
    date_start = fields.Date(string='Fecha de Inicio', default=fields.Date.context_today)
    date_end = fields.Date(string='Fecha de End', default=fields.Date.context_today)
    total_goal = fields.Boolean(compute='_compute_total_goal', string='Total Goal')
        
    @api.depends('total_amount', 'total_goal')
    def _compute_total_goal(self):
        for record in self:
            # Encuentra el total
            move_ids = self.env['account.move'].search([('team_id', '=', record.crm_team_id.id),
                                                    ('date', '>=', record.date_start),
                                                    ('date', '<=', record.date_end),
                                                    ('state', '<=', 'posted'),
                                                    ('move_type', '<=', 'out_invoice'),
                                                    ('invoice_user_id', '=', record.user_id.id)], order="id asc")
            record.total_invoice = sum(move_ids.mapped('amount_untaxed'))
            record.total_goal = True
