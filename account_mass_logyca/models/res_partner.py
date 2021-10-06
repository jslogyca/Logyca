# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    logycax_discount_id = fields.Many2one('config.discount.logycaedx', string='LogycaX Discount', tracking=True)
