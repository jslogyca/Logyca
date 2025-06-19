# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_gs1_id = fields.Many2one('sale.order', string='Cotización')
    second_gs1 = fields.Boolean('Segundo Comunicado GS1 GS1', default=False)
    date_second_gs1 = fields.Date(string='Fecha Segundo Comunicado GS1')

    def check_second_gs1(self):
        date = fields.Datetime.now()
        for sale_gs1 in self:
            sale_gs1_id = self._check_sale_second_gs1()
            if sale_gs1_id:
                sale_gs1.write({'second_gs1': True, 'date_second_gs1': sale_gs1_id.create_date, 'sale_gs1_id': sale_gs1_id.id})
            else:
                sale_gs1.write({'second_gs1': False, 'date_second_gs1': None})

    def _check_sale_second_gs1(self):
        sale_template = self.env['sale.order.template'].search([('second_gs1', '=', True)], limit=1)
        if sale_template:
            sale_order = self.env['sale.order'].search([('partner_id', '=', self.id), 
                                                            ('sale_order_template_id', '=', sale_template.id),
                                                            ('date_order', '>=', '2025-01-01')], limit=1)
            if sale_order:
                return sale_order
