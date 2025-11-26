# -*- coding: utf-8 -*-


from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class SalesOrder(models.Model):
    _inherit = 'sale.order'

    date_init_member_test = fields.Date(string='Inicio Periodo de Prueba Membresía', default=fields.Date.context_today)
    date_end_member_test = fields.Date(string='Final Periodo de Prueba Membresía', default=fields.Date.context_today)
    free_member = fields.Boolean(string='Periodo de Prueba', default=False)

    def action_order_member(self):
        for order in self:
            date_end_member_test = order.date_init_member_test + timedelta(days=90)
            product_id = None
            if order.partner_id and order.partner_id.rango_type:
                product_id = self.env['product.product'].search([('rango_type', '=', order.partner_id.rango_type)], limit=1)
            else:
                product_id = self.env['product.product'].search([('rango_type', '=', 'comercio')], limit=1)
            team_id = self.env['crm.team'].search([('free_member', '=', True)])
            user_id = order.user_id
            if order.partner_id.how_findout=='asesor1':
                user_id = self.env['crm.team.member'].search([('free_member_one', '=', True)])
            elif order.partner_id.how_findout=='asesor2':
                user_id = self.env['crm.team.member'].search([('free_member_two', '=', True)])
            else:
                user_id = self.env['crm.team.member'].search([('free_member_shop', '=', True)])

            self._cr.execute(''' UPDATE sale_order SET note='Estoy de acuerdo con la Autorización del Sistema de administración de riesgo de lavado de activos y de la financiación del terrorismo - SARLAFT',
                                payment_term_id=31, company_id=2, free_member=%s, date_end_member_test=%s WHERE id=%s ''', (True, date_end_member_test, order.id))
            # self._cr.execute(''' UPDATE sale_order SET payment_term_id=10, company_id=2, free_member=%s, date_end_member_test=%s WHERE id=%s ''', (True, date_end_member_test, order.id))
            self._cr.execute(''' UPDATE sale_order_line SET analytic_distribution = '{"618": 100.0}', company_id=2 WHERE order_id=%s ''', (order.id,))
            if team_id:
                self._cr.execute(''' UPDATE sale_order SET team_id=%s WHERE id=%s ''', (team_id.id, order.id,))
            if user_id:
                self._cr.execute(''' UPDATE sale_order SET user_id=%s WHERE id=%s ''', (user_id.user_id.id, order.id,))
            if product_id:
                self._cr.execute(''' UPDATE sale_order_line SET product_id=%s WHERE order_id=%s ''', (product_id.id, order.id,))
            
            self.action_create_partner(order.partner_id)
            if order.partner_id.parent_id:
                vinculation_type_id = self.env['logyca.vinculation_types'].search([('membertyb', '=', True)])
                order.partner_id.parent_id.x_type_vinculation = vinculation_type_id
                order.partner_id.parent_id.write({'x_active_vinculation': True,
                                                    'x_date_vinculation': order.date_init_member_test,
                                                    'date_init_member_test': order.date_init_member_test,
                                                    'date_end_member_test': date_end_member_test})
                self._cr.execute(''' UPDATE sale_order SET partner_id=%s WHERE id=%s ''', (order.partner_id.parent_id.id, order.id,))
            template = self.env.ref('member_logyca.mail_template_member_welcome')
            template.send_mail(order.id, force_send=True)            
            template = self.env.ref('member_logyca.email_template_sale_order_loyalty')
            template.send_mail(order.id, force_send=True)            

    
    def action_create_partner(self, partner):
        partner.create_company()

    def _send_payment_succeeded_for_order_mail(self):
        """ Send a mail to the SO customer to inform them that a payment has been initiated.

        :return: None
        """
        if self.website_id:
            self.action_order_member()
            print('ENVIO CORREO', self)
            mail_template = self.env.ref(
                'member_logyca.mail_template_sale_payment_executed_website', raise_if_not_found=False
            )
            for order in self:
                order._send_order_notification_mail(mail_template)            
        else:
            mail_template = self.env.ref(
                'sale.mail_template_sale_payment_executed', raise_if_not_found=False
            )
            for order in self:
                order._send_order_notification_mail(mail_template)
