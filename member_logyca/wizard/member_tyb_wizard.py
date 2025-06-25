# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils
from dateutil.relativedelta import relativedelta

import base64


class MemberTYBWizard(models.TransientModel):
    _name = 'member.tyb.wizard'
    _description = 'Member TYB Wizard'


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    date = fields.Date(string='Fecha Incio Membresía', default=fields.Date.context_today)

    def save_detail_advance(self):
        self.ensure_one()
        # 1) Tipo de vinculación
        obj_type_vinculation = self.env['logyca.vinculation_types'].search(
            [('membertyb', '=', True)], order="id asc", limit=1)

        # 2) Obtener el partner activo
        partner = self.env['res.partner'].browse(self._context.get('active_id'))
        if partner:
            # 3) Marcar vinculación en partner
            partner_vals = {
                'x_active_vinculation': True,
                'x_date_vinculation': self.date,
                'x_type_vinculation': obj_type_vinculation,
            }
            partner.write(partner_vals)

            # 4) Crear la orden de venta
            date_end = self.date + relativedelta(months=3)
            sale_vals = {
                'partner_id': partner.id,
                'client_order_ref': 'Membresía TYB',
                'partner_invoice_id': partner.id,
                'x_type_sale': 'Renovación',
                'validity_date': date_end,
                'date_order': self.date,
                'date_init_member_test': self.date,
                'date_end_member_test': date_end,
                'free_member': True,

            }
            sale = self.env['sale.order'].create(sale_vals)

            # 5) Agregar la línea de venta
            line_vals = {
                'order_id': sale.id,
                'product_id': 1,          # sustituye por el ID correcto
                'product_uom_qty': 1,
                'price_unit': 350000,
            }
            self.env['sale.order.line'].create(line_vals)

            # 6) Devolver la acción para abrir el form de sale.order
            return {
                'type': 'ir.actions.act_window',
                'name': 'Orden de Venta',
                'res_model': 'sale.order',
                'res_id': sale.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
            }

        # Si no hay partner, simplemente cerramos el wizard
        return {'type': 'ir.actions.act_window_close'}
