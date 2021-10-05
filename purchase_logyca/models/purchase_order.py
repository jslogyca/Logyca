# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    ok_invoice = fields.Boolean(string='Ok Invoice', default=False, tracking=True,)
