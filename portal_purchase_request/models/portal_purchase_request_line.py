"""Portal Purchase Request Line Model"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PortalPurchaseRequestLine(models.Model):
    _name = "portal.purchase.request.line"
    _description = "Portal purchase request line"

    request_id = fields.Many2one(
        "portal.purchase.request", string="Request", ondelete="cascade"
    )
    description = fields.Char(string="Description")
    quantity = fields.Float(string="Quantity", default=1.0)

    # Constraints functions

    @api.constrains("quantity")
    def _check_product(self):
        """Ensure quantity is positive and greater than zero"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(
                    _("Quantity must be positive and greater than zero.")
                )
