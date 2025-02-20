# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_vinculation_types(models.Model):
    _inherit = 'logyca.vinculation_types'

    tag_id = fields.Many2one('res.partner.category', string='Categotía')
