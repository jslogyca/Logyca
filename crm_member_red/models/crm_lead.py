# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _


class CRMLead(models.Model):
    _inherit = 'crm.lead'

    member_red_id = fields.Many2one('logyca.member.red', string='Red de Valor')

    @api.depends('partner_id')
    def _compute_member_red(self):
        """ compute the new values when partner_id has changed """
        for lead in self:
            if lead.partner_id:
                lead.member_red_id = lead.partner_id.member_red_id


    @api.depends('partner_id')
    def _compute_title(self):
        # Llamar a la lógica original
        super()._compute_title()
        # Lógica adicional: ejemplo, registrar log si no hay título
        for lead in self:
            if lead.partner_id:
                lead.member_red_id = lead.partner_id.member_red_id