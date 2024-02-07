# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    marketplace_ids = fields.One2many('rel.res.partner.marketplace', "partner_id", string="Marketplaces", copy=False,)
