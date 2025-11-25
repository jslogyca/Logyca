# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_expense_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador de Gastos por Defecto',
        related='company_id.default_expense_approver_id', readonly=False, check_company=True
    )
