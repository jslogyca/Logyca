# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
import requests
import datetime
import base64
import json

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal')
    type_accountant = fields.Selection(related='product_id.type_accountant', store=True)

    @api.onchange('product_id')
    def _onchange_product_line(self):
        for line in self:
            if line.product_id.type_accountant == 'costo' :
                budget_group = self.env['logyca.budget_group'].search([('by_default_group', '=', True), 
                                        ('company_id', '=', line.company_id.id)], order="id asc", limit=1)
                if budget_group:
                    line.x_budget_group = budget_group

    @api.onchange('x_budget_group')
    def onchange_budget_group(self):
        if self.x_budget_group:
            self.analytic_distribution = self.x_budget_group.analytic_distribution
        else:
            self.analytic_distribution = False

    @api.constrains('analytic_distribution')
    def _check_analytic_distribution(self):
        for record in self:
            if record.analytic_distribution:
                total = sum(record.analytic_distribution.values())
                if total > 100:
                    raise ValidationError(
                            f"La distribución analítica no puede superar el 100%. "
                            f"Actualmente suma: {total:.2f}%. Verifique la línea con el producto: {record.product_id.display_name or 'Sin producto'}.")

    def _prepare_account_move_line(self, move=False):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        res = {
            'display_type': self.display_type or 'product',
            'name': '%s: %s' % (self.order_id.name, self.name),
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.currency_id._convert(self.price_unit, aml_currency, self.company_id, date, round=False),
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
            'x_budget_group': self.x_budget_group.id,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res
