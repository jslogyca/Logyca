# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import re
import logging

class RVCTemplateEmailWizard(models.TransientModel):
    _name = "rvc.template.email.wizard"
    _rec_name = 'id'


    note_deactive = fields.Text(string='Nota Adicional')
    email_credentials = fields.Char(string="Email Credenciales")

    def action_reason_desactive(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if partner and benefit_application.contact_email:

                # notificar Derechos de Identificación
                if benefit_application.product_id.code == '01':
                    access_link = partner._notify_get_action_link('view')
                    template = self.env.ref('rvc.mail_template_notify_benefit_codes')
                    subject = "Beneficio Derechos de Identificación"
                    template.with_context(url=access_link).send_mail(benefit_application.id, force_send=False, email_values={'subject': subject})
                    benefit_application.write({'state': 'notified', 'notification_date': datetime.now()})

                # notificar Logyca/colabora para los que tienen GLN
                elif benefit_application.product_id.code == '02' and benefit_application._validate_gln():
                    access_link = partner._notify_get_action_link('view')
                    template = self.env.ref('rvc.mail_template_notify_benefit_colabora')
                    subject = "Beneficio Plataforma LOGYCA / COLABORA"
                    template.with_context(url=access_link).send_mail(benefit_application.id, force_send=False, email_values={'subject': subject})
                    benefit_application.write({'state': 'notified', 'notification_date': datetime.now()})

                 # notificar Logyca/colabora para los que NO tienen GLN
                elif benefit_application.product_id.code == '02' and benefit_application._validate_gln() == False:
                    access_link = partner._notify_get_action_link('view')
                    template = self.env.ref('rvc.mail_template_notify_benefit_codes')
                    subject = "Beneficio Plataforma LOGYCA / COLABORA"
                    template.with_context(url=access_link).send_mail(benefit_application.id, force_send=False, email_values={'subject': subject})
                    benefit_application.write({'state': 'notified', 'notification_date': datetime.now()})

        return {'type': 'ir.actions.act_window_close'}


    def action_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            benefit_application.message_post(body=_(\
                    '%s <u><strong>ACEPTÓ</strong></u> el beneficio.' % str(benefit_application.partner_id.partner_id.name)))

            if benefit_application.product_id.benefit_type == 'codigos':
                benefit_application.attach_OM_2_partner(benefit_application)

            if benefit_application.product_id.benefit_type == 'colabora':
                benefit_application.calculate_end_date_colabora()

            benefit_application.write({'state': 'confirm', 'acceptance_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}

    def action_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if benefit_application.partner_id.contact_email:
                access_link = partner._notify_get_action_link('view')

                if benefit_application.product_id.benefit_type == 'codigos':
                    template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                elif benefit_application.product_id.benefit_type == 'colabora':
                    template = self.env.ref('rvc.mail_template_welcome_kit_colabora_rvc')
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    template = self.env.ref('rvc.mail_template_welcome_kit_digital_card_rvc')

                # adjuntar la OM al kit de bienvenida si no se postuló desde Odoo 
                if benefit_application.origin != 'odoo':
                    template= benefit_application.create_OM_attachment(template)
                else:
                    template.attachment_ids = False

                template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)

                if not benefit_application.gln:
                    # si no tiene GLN, asignamos uno.
                    if benefit_application._validate_gln() == False and benefit_application.glns_codes_quantity == 0:
                        benefit_application.assignate_gln_code()

                if benefit_application.product_id.benefit_type == 'codigos':
                    # codigos glns
                    if benefit_application.glns_codes_quantity > 0:
                        benefit_application.assignate_gln_code(benefit_application.glns_codes_quantity)

                    # codigos recaudo
                    if benefit_application.invoice_codes_quantity > 0:
                        benefit_application.assign_invoice_codes()

                    # Asignar beneficio de códigos de identificación
                    if benefit_application.codes_quantity > 0:
                        if benefit_application.assign_identification_codes():
                            benefit_application.assign_credentials_colabora()

                    # Agregar tipo de vinculacion al tercero
                    benefit_application.add_vinculation_partner()

                elif benefit_application.product_id.benefit_type == 'colabora':
                    # Activar colabora
                    if benefit_application.assign_colabora():
                        benefit_application.assign_credentials_colabora()

                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    benefit_application.send_digital_cards_bearer(template)

                #Actualizar Contacto y Empresa
                benefit_application.update_contact(benefit_application.partner_id)
                if benefit_application.parent_id:
                    benefit_application.update_company(benefit_application)

                benefit_application.write({'state': 'done'})
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))

        return {'type': 'ir.actions.act_window_close'}

    def action_re_done(self):
        """
        forward email kit notification
        <important> this function don't assign codes, colabora or analytica.</important>
        """
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if benefit_application.partner_id.contact_email:
                access_link = partner._notify_get_action_link('view')

                if benefit_application.product_id.benefit_type == 'codigos':
                    template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                elif benefit_application.product_id.benefit_type == 'colabora':
                    template = self.env.ref('rvc.mail_template_welcome_kit_colabora_rvc')
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    template = self.env.ref('rvc.mail_template_welcome_kit_digital_card_rvc')

                # adjuntar la OM al kit de bienvenida si no se postuló desde Odoo
                if benefit_application.origin != 'odoo':
                    template= benefit_application.create_OM_attachment(template)
                else:
                    template.attachment_ids = False

                try:
                    template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)
                    benefit_application.message_post(body=_(\
                    'Se <strong>REENVIÓ</strong></u> el kit de bienvenida del beneficio.'))
                except:
                    benefit_application.message_post(body=_(\
                    'No se pudo <strong>REENVIAR</strong></u> el kit de bienvenida del beneficio %s.' % str(benefit_application.product_id.benefit_type)))

                #Enviando tarjetas
                if benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    benefit_application.send_digital_cards_bearer(template)
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))

        return {'type': 'ir.actions.act_window_close'}

    def action_rejected(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            benefit_application.write({'state': 'rejected', 'rejection_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}

    def re_assign_credentials(self):
        for rec in self:
            if rec.email_credentials != False:
                logging.info(rec.email_credentials)
                match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(rec.email_credentials).lower())

                if match == None:
                    raise UserError(f"El email '{str(rec.email_credentials).lower()}' NO es válido. Por favor verifíquelo.")

                context = dict(self._context or {})
                active_ids = context.get('active_ids', []) or []
                active_id = context.get('active_ids', False)
                benefit_application = self.env['benefit.application'].browse(active_id)
                if benefit_application:
                    benefit_application.assign_credentials_colabora(re_assign=True, re_assign_email=rec.email_credentials)
        return True