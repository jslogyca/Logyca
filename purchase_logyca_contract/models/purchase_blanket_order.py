# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class PurchaseBlanketOrder(models.Model):
    _inherit = 'purchase.blanket.order'

    order_type = fields.Many2one('purchase.order.type', string='Type', domain="[('company_id', 'in', [False, company_id])]", states={"draft": [("readonly", False)]})
    duration_day = fields.Float('Duration Days', default=0.0, states={"draft": [("readonly", False)]})
    duration_month = fields.Float('Duration Month', default=0.0, states={"draft": [("readonly", False)]})
    url = fields.Char('URL', states={"draft": [("readonly", False)]})
