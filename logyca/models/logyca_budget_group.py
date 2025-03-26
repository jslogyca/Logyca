# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_budget_group(models.Model):
    _name = 'logyca.budget_group'
    _description = 'Grupos presupuestal'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    # lser_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Servicios', domain="[('company_id', '=', 1)]")
    # iac_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Asociación', domain="[('company_id', '=', 2)]")
    # log_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Investigación', domain="[('company_id', '=', 3)]")

    def name_get(self):
        return [(record.id, '%s - %s' %
                 (record.code, record.name)) for record in self]
