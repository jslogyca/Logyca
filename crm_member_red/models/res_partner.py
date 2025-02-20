# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    member_red_id = fields.Many2one('logyca.member.red', string='Red de Valor')
