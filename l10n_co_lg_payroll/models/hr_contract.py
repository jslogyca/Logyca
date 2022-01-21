# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRContract(models.Model):
    _inherit = 'hr.contract'

    contract_integral = fields.Boolean('Integral Contract', default=False)
    pensionado = fields.Boolean('Pensionado', default=False)
    risk_id = fields.Many2one('hr.risk', string='Risk')
