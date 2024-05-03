# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    allies_logyca = fields.Boolean('Allies Logyca', default=False)
    allies_user_id = fields.Many2one('res.partner')
    benefits_ids = fields.One2many('benefits.membership.partner', 'partner_id', string="Benefits", index=True)
