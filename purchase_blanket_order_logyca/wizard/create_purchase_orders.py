# Copyright (C) 2018 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BlanketOrderWizard(models.TransientModel):
    _inherit = "purchase.blanket.order.wizard"

    notes = fields.Text('Observaciones')    

    def create_purchase_order(self):
        order_lines_by_supplier = defaultdict(list)
        currency_id = 0
        payment_term_id = 0
        for line in self.line_ids:
            if line.qty == 0.0:
                continue

            if line.qty > line.remaining_uom_qty:
                raise UserError(_("You can't order more than the remaining quantities"))

            date_planned = line.blanket_line_id.date_schedule
            vals = {
                "product_id": line.product_id.id,
                "name": line.product_id.name,
                "date_planned": date_planned
                if date_planned
                else line.blanket_line_id.order_id.date_start,
                "product_uom": line.product_uom.id,
                "sequence": line.blanket_line_id.sequence,
                "price_unit": line.blanket_line_id.price_unit,
                "blanket_order_line": line.blanket_line_id.id,
                "product_qty": line.qty,
                "taxes_id": [(6, 0, line.taxes_id.ids)],
                "analytic_distribution": line.blanket_line_id.order_id.analytic_distribution,
                "x_budget_group": line.blanket_line_id.order_id.budget_group_id.id,
            }
            order_lines_by_supplier[line.partner_id.id].append((0, 0, vals))

            if currency_id == 0:
                currency_id = line.blanket_line_id.order_id.currency_id.id
            elif currency_id != line.blanket_line_id.order_id.currency_id.id:
                currency_id = False

            if payment_term_id == 0:
                payment_term_id = line.blanket_line_id.payment_term_id.id
            elif payment_term_id != line.blanket_line_id.payment_term_id.id:
                payment_term_id = False

        if not order_lines_by_supplier:
            raise UserError(_("An order can't be empty"))

        if not currency_id:
            raise UserError(
                _(
                    "Can not create Purchase Order from Blanket "
                    "Order lines with different currencies"
                )
            )

        res = []
        for supplier in order_lines_by_supplier:
            order_vals = {
                "partner_id": int(supplier),
            }
            if self.blanket_order_id:
                order_vals.update(
                    {
                        "partner_ref": self.blanket_order_id.partner_ref,
                        "origin": self.blanket_order_id.name,
                        "notes": self.notes + ' - ' + self.blanket_order_id.note,
                    }
                )
            order_vals.update(
                {
                    "currency_id": currency_id if currency_id else False,
                    "payment_term_id": (payment_term_id if payment_term_id else False),
                    "order_line": order_lines_by_supplier[supplier],
                }
            )
            purchase_order = self.env["purchase.order"].create(order_vals)
            res.append(purchase_order.id)
        return {
            "domain": [("id", "in", res)],
            "name": _("RFQ"),
            "view_mode": "tree,form",
            "res_model": "purchase.order",
            "view_id": False,
            "context": {"from_purchase_order": True},
            "type": "ir.actions.act_window",
        }

