"""Purchase Order model extension for portal purchase requests"""

from odoo import _, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    portal_request_id = fields.Many2one(
        "portal.purchase.request", string="Portal Request", readonly=True
    )

    # Override methods

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            if order.portal_request_id:
                order.portal_request_id.state = "in_process"
                purchases = self.env["purchase.order"].search(
                    [
                        ("portal_request_id", "=", order.portal_request_id.id),
                        ("state", "not in", ["cancel", "done"]),
                        ("id", "!=", order.id),
                    ]
                )
                if purchases:
                    purchases.write(
                        {
                            "x_reason_cancellation": _(
                                "Cancelled by another purchase order confirmation from the same request."
                            )
                        }
                    )
                    purchases.button_cancel()
        return res

    def action_create_invoice(self):
        res = super().action_create_invoice()
        for order in self:
            if order.portal_request_id:
                order.portal_request_id.state = "completed"
                order.portal_request_id.completion_date = fields.Date.today()
        return res
