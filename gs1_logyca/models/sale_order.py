# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SalesOrder, self).action_confirm()
        for order in self:
            order.partner_id.sudo().write({
                'sale_gs1_id': order.id,
                'second_gs1': True,
                'date_second_gs1': order.create_date,
            })        
        return res
