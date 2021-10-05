# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_cargo_directivo = fields.Boolean(string='Cargo Directivo', default=False)

