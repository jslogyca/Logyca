# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    seller = fields.Boolean('Seller', default=False, tracking=True)
