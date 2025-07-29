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
