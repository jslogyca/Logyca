# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_budget_group(models.Model):
    _name = 'logyca.budget_group'
    _inherit = 'analytic.mixin'
    _description = 'Grupos presupuestal'
    _check_company_auto = True

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company.id)
    by_default_group = fields.Boolean('Por Defecto', default=False)

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.code, record.name)) for record in self]
