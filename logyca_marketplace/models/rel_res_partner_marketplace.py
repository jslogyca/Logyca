# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
from odoo.modules.module import get_module_resource


class RelResPartnerMarketplace(models.Model):
    _name = 'rel.res.partner.marketplace'
    _description = 'Marketplace - Partner'

    partner_id = fields.Many2one('res.partner', string='Seller', ondelete='restrict')
    marketplace_id = fields.Many2one('res.partner.marketplace', string="Marketplace", copy=False,)
    name = fields.Char(string='Name')

    def name_get(self):
        return [(marketplace.id, '%s' % (marketplace.marketplace_id.partner_id.name)) for marketplace in self]
