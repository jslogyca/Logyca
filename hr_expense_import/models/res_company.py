# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    default_expense_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador de Gastos por Defecto', check_company=True
    )