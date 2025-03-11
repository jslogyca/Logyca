# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    follow_ids = fields.One2many('follow.partner.loyalty', 'partner_id', string="Fidelización", index=True)

