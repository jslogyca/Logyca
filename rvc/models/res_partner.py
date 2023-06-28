# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_is_seller = fields.Boolean('Seller', default=False, tracking=True, help="La empresa vende en el marketplace del éxito?")
