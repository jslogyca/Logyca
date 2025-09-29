"""Purchase Order Wizard and Lines"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrderWizard(models.TransientModel):
    _name = "purchase.order.wizard"
    _inherit = ["analytic.mixin"]
    _description = "Purchase Order Wizard"

    purchase_request_id = fields.Many2one(
        "portal.purchase.request", string="Purchase Request", required=True
    )
    partner_id = fields.Many2one("res.partner", string="Vendor", required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    budget_group_id = fields.Many2one("logyca.budget_group", string="Budget Group")
    request_line_ids = fields.One2many(
        "portal.purchase.request.line",
        related="purchase_request_id.product_line_ids",
        string="Request Products",
        readonly=True,
    )
    line_ids = fields.One2many(
        "purchase.order.wizard.line", "wizard_id", string="Products"
    )

    # Onchange methods

    @api.onchange("budget_group_id")
    def _onchange_budget_group(self):
        """Update analytic distribution based on selected budget group"""
        for rec in self:
            if rec.budget_group_id:
                rec.analytic_distribution = rec.budget_group_id.analytic_distribution
            else:
                rec.analytic_distribution = False

    # Business methods

    def action_create_purchase_order(self):
        """Create a purchase order from the wizard data"""
        self.ensure_one()
        error_list = []
        if not self.request_line_ids:
            error_list.append(_("You must select at least one request line.\n"))

        if not self.line_ids:
            error_list.append(
                _("You must select at least one product to create a purchase order.\n")
            )

        for line in self.line_ids:
            if line.product_qty <= 0:
                error_list.append(_("Quantity must be positive and greater than zero."))

        if error_list:
            raise ValidationError("".join(error_list))

        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner_id.id,
                "currency_id": self.currency_id.id,
                "date_order": fields.Date.context_today(self),
                "company_id": self.purchase_request_id.company_id.id,
                "origin": self.purchase_request_id.name,
                "portal_request_id": self.purchase_request_id.id,
            }
        )

        for line in self.line_ids:
            self.env["purchase.order.line"].create(
                {
                    "order_id": purchase_order.id,
                    "product_id": line.product_id.id,
                    "name": line.name,
                    "product_qty": line.product_qty,
                    "price_unit": line.price_unit,
                    "taxes_id": [(6, 0, line.taxes_ids.ids)],
                    "x_budget_group": self.budget_group_id.id or False,
                    "analytic_distribution": self.analytic_distribution or False,
                }
            )

        self.purchase_request_id.state = "to_invoice"

        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Order"),
            "res_model": "purchase.order",
            "res_id": purchase_order.id,
            "view_mode": "form",
            "target": "current",
        }


class PurchaseOrderWizardLine(models.TransientModel):
    _name = "purchase.order.wizard.line"
    _description = "Purchase Order Wizard Line"

    wizard_id = fields.Many2one(
        "purchase.order.wizard", string="Wizard", ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product", required=True)
    name = fields.Text(string="Description", required=True)
    product_qty = fields.Float(string="Quantity", default=1.0, required=True)
    price_unit = fields.Float(string="Unit Price", required=True)
    taxes_ids = fields.Many2many(
        "account.tax", string="Taxes", domain="[('type_tax_use', '=', 'purchase')]"
    )
    price_subtotal = fields.Monetary(
        string="Subtotal", compute="_compute_amount", store=True
    )
    price_total = fields.Monetary(string="Total", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(related="wizard_id.currency_id", string="Currency")

    @api.depends("product_qty", "price_unit", "taxes_ids")
    def _compute_amount(self):
        """Compute subtotal and total amounts considering taxes"""
        for line in self:
            taxes = line.taxes_ids.compute_all(
                line.price_unit,
                line.currency_id,
                line.product_qty,
                product=line.product_id,
            )
            line.price_subtotal = taxes["total_excluded"]
            line.price_total = taxes["total_included"]

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Update description, unit price, and taxes based on selected product"""
        if self.product_id:
            self.name = self.product_id.name
            self.price_unit = self.product_id.list_price
            if self.product_id.supplier_taxes_id:
                self.taxes_ids = self.product_id.supplier_taxes_id

    @api.constrains("product_qty", "price_unit")
    def _check_values(self):
        """Ensure quantity is positive and unit price is non-negative"""
        for line in self:
            if line.product_qty <= 0:
                raise ValidationError(
                    _("Quantity must be positive and greater than zero.")
                )
            if line.price_unit < 0:
                raise ValidationError(_("Unit price cannot be negative."))
