# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    legal_representative = fields.Many2one('res.partner', string='Legal Representative')
