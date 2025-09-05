# Copyright (C) 2018 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _get_type_id(self):
        return self.env['purchase.blanket.order.type'].search([], limit=1)

    type_blanket_id = fields.Many2one('purchase.blanket.order.type', string="Agreement Type", required=True, default=_get_type_id)
    contract_over = fields.Boolean(
        string="Excede contrato",
        compute="_compute_contract_over",
        store=True
    )
    contract_over_msg = fields.Char(
        string="Advertencia contrato",
        compute="_compute_contract_over",
        store=True
    )
    approval_type = fields.Selection(related='blanket_order_id.approval_type')    

    @api.depends(
        'amount_total', 'currency_id', 'date_order', 'company_id',
        'blanket_order_id',
        'blanket_order_id.amount_invoice_pend',
        'blanket_order_id.percent_pend_invoiced',
        'blanket_order_id.amount_total',
        'blanket_order_id.amount_untaxed',
        'blanket_order_id.currency_id',
    )
    def _compute_contract_over(self):
        for order in self:
            over = False
            msg_parts = []
            contract = order.blanket_order_id

            if contract:
                # Cantidades y monedas
                po_amount = order.amount_untaxed
                po_curr = order.currency_id
                ct_curr = getattr(contract, 'currency_id', False)
                # Convertir el monto del pedido a la moneda del contrato (si difiere)
                if ct_curr and po_curr and ct_curr != po_curr:
                    po_amount_conv = po_curr._convert(
                        po_amount, ct_curr, order.company_id,
                        order.date_order or fields.Date.context_today(order)
                    )
                else:
                    po_amount_conv = po_amount

                # 1) Validar por MONTO pendiente
                amt_pend = getattr(contract, 'amount_invoice_pend', None)
                if isinstance(amt_pend, (int, float)):
                    if po_amount_conv > (amt_pend or 0.0) + 1e-6:
                        over = True
                        msg_parts.append(
                            "monto del pedido ({:.2f} {}) > pendiente ({:.2f} {})".format(
                                po_amount_conv,
                                ct_curr.name if ct_curr else order.company_id.currency_id.name,
                                amt_pend,
                                ct_curr.name if ct_curr else order.company_id.currency_id.name,
                            )
                        )

                # 2) Validar por PORCENTAJE pendiente (si hay total de contrato)
                pct_pend = getattr(contract, 'percent_pend_invoiced', None)
                total_contract = (
                    getattr(contract, 'amount_total', None)
                    or getattr(contract, 'amount_untaxed', None)
                )
                if pct_pend is not None:
                    try:
                        pct_pend = float(pct_pend)
                    except Exception:
                        pct_pend = None

                if pct_pend is not None:
                    if isinstance(total_contract, (int, float)) and total_contract:
                        required_pct = 100.0 * po_amount_conv / float(total_contract)
                        if required_pct > pct_pend:
                            over = True
                            msg_parts.append(
                                "porcentaje requerido ({:.2f}%) > pendiente ({:.2f}%)".format(
                                    required_pct, pct_pend
                                )
                            )
                    else:
                        # Si no tenemos total del contrato, asumimos que 0% pendiente => agotado
                        if pct_pend <= 0.0:
                            over = True
                            msg_parts.append("porcentaje pendiente agotado ({:.2f}%)".format(pct_pend))

            order.contract_over = over
            order.contract_over_msg = (
                "Este pedido de compra supera el tope del contrato: " + "; ".join(msg_parts)
                if over else False
            )

