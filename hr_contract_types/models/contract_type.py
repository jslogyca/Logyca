# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ContractType(models.Model):
    _inherit = 'hr.contract.type'

    sequence = fields.Integer(help="Gives the sequence when displaying a list of Contract.", default=10)


class ContractInherit(models.Model):
    _inherit = 'hr.contract'

    type_id = fields.Many2one('hr.contract.type', string="Employee Category",
                              required=True, help="Employee category",
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))
