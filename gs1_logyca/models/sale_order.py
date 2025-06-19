# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SalesOrder, self).action_confirm()
        self.partner_id.sale_gs1_id = self.id
        self.partner_id.second_gs1 = True
        self.partner_id.date_second_gs1 = self.create_date
        return res
