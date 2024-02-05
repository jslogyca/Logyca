# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo.modules.module import get_module_resource


class ResPartnerMarketplace(models.Model):
    _name = 'res.partner.marketplace'
    _description = 'Marketplace'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', string='Empresa MarketPlace', tracking=True, ondelete='restrict')
    active = fields.Boolean('Active', default=True)
    name = fields.Char(string='Name', tracking=True)
    seller_ids = fields.One2many('rel.res.partner.marketplace', "marketplace_id", string="Sellers", copy=False,)

    def name_get(self):
        return [(marketplace.id, '%s - %s' % (marketplace.partner_id.name, marketplace.partner_id.vat)) for marketplace in self]
