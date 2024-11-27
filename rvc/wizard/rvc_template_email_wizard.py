# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from ..models import rvc_activations
import re
import logging


class RVCTemplateEmailWizard(models.TransientModel):
    _name = "rvc.template.email.wizard"
    _description = 'RVC Template Email Wizard'
    _rec_name = 'id'

    note_deactive = fields.Text(string='Nota Adicional')
    email_credentials = fields.Char(string="Email Credenciales")
    date_done_cons = fields.Date(string='Date Solución', default=fields.Date.context_today)
    
    def action_reason_desactive(self):
        context = dict(self._context or {})
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
                elif benefit_application.product_id.code == '02' and benefit_application._validate_gln() is False:
                    access_link = partner._notify_get_action_link('view')
                    template = self.env.ref('rvc.mail_template_notify_benefit_codes')
                    subject = "Beneficio Plataforma LOGYCA / COLABORA"
                    template.with_context(url=access_link).send_mail(benefit_application.id, force_send=False, email_values={'subject': subject})
                    benefit_application.write({'state': 'notified', 'notification_date': datetime.now()})

        return {'type': 'ir.actions.act_window_close'}


    def action_confirm(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            if benefit_application.product_id.benefit_type == 'crece_mype':
                benefit_application._send_assing_crece_mype()
                benefit_application._get_employe(benefit_application.email_employee)
            else:
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
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            contact_email = benefit_application.partner_id.contact_email
            if contact_email:
                if benefit_application.product_id.benefit_type == 'codigos':
                    activated = rvc_activations.activate_gs1_codes(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de Códigos GS1.'))
                elif benefit_application.product_id.benefit_type == 'colabora':
                    activated = rvc_activations.activate_logyca_colabora(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de la plataforma LOGYCA / COLABORA.'))
                    else:
                        benefit_application.message_post(body=_(\
                            '🚫 No se pudo <strong>solicitar la activación</strong></u> de la plataforma LOGYCA / COLABORA.'))
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    if benefit_application.digital_card_ids:
                        activated = rvc_activations.activate_digital_cards(benefit_application)
                        if activated:
                            benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de Tarjetas Digitales.'))
                    else:
                        raise ValidationError(
                            _('¡Error! No hay tarjetas digitales para generar 😔.\n\nPara solicitarlas: \n'
                              '1. Active el modo edición yendo al botón EDITAR del lado superior izquierdo.\n'
                              '2. Vaya a la sección de Tarjetas Digitales.\n'
                              '3. Pulse la opción "Agregar línea."')
                        )

                benefit_application.write({'state': 'done', 'delivery_date': datetime.now()})
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))

        return {'type': 'ir.actions.act_window_close'}

    def action_done_mass(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            for benefit in benefit_application:
                partner=self.env['res.partner'].search([('id','=',benefit.partner_id.partner_id.id)])
                if benefit.partner_id.contact_email:
                    access_link = partner._notify_get_action_link('view')

                    if benefit.product_id.benefit_type == 'codigos':
                        if benefit.is_seller:
                            template = self.env.ref('rvc.mail_template_welcome_kit_rvc_seller')
                        else:
                            template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                    elif benefit.product_id.benefit_type == 'colabora':
                        template = self.env.ref('rvc.mail_template_welcome_kit_colabora_rvc')
                    elif benefit.product_id.benefit_type == 'tarjeta_digital':
                        template = self.env.ref('rvc.mail_template_welcome_kit_digital_card_rvc')
                    else:
                        template=None

                    # adjuntar la OM al kit de bienvenida si no se postuló desde Odoo 
                    if template:
                        if benefit.origin != 'odoo':
                            #se usa para eliminar los adjuntos de la plantilla de correo
                            template.attachment_ids = [(5,)]
                            template= benefit.create_OM_attachment(template)
                        else:
                            template.attachment_ids = False

                    # Se envía kit de bienvenida
                    # excepto si es tarjeta digital, en ese caso el beneficio se activa primero y DESPUÉS enviamos kit con 
                    # la funcion send_digital_cards_bearer()
                    try:
                        if benefit.product_id.benefit_type not in ('tarjeta_digital', 'colabora'):
                            template.with_context(url=access_link).send_mail(benefit.id, force_send=True)
                            #se usa para eliminar los adjuntos de la plantilla de correo
                            template.attachment_ids = [(5,)]
                    except Exception as e:
                        benefit.message_post(body=_(f'No se pudo <strong>Enviar</strong></u> el kit de bienvenida del beneficio {benefit.product_id.benefit_type}. Error: {e}'))

                    if not benefit.gln:
                        # si no tiene GLN, asignamos uno.
                        if benefit._validate_gln() is False and benefit.glns_codes_quantity == 0:
                            benefit.assignate_gln_code()

                    if benefit.product_id.benefit_type == 'codigos':
                        # codigos glns
                        if benefit.glns_codes_quantity > 0:
                            if benefit.send_kit_with_no_benefit is False:
                                if benefit.assignate_gln_code(benefit.glns_codes_quantity):
                                    benefit.assign_credentials_gs1codes()
                            else:
                                benefit.assign_credentials_gs1codes()
                        # codigos recaudo
                        if benefit.invoice_codes_quantity > 0:
                            if benefit.send_kit_with_no_benefit is False:
                                if benefit.assign_invoice_codes():
                                    benefit.assign_credentials_gs1codes()
                            else:
                                benefit.assign_credentials_gs1codes()
                        # codigos producto
                        if benefit.codes_quantity > 0:
                            if benefit.send_kit_with_no_benefit is False:
                                if benefit.assign_identification_codes():
                                    benefit.assign_credentials_gs1codes()
                            else:
                                benefit.assign_credentials_gs1codes()

                        # Agregar tipo de vinculacion al tercero
                        benefit.add_vinculation_partner()

                    elif benefit.product_id.benefit_type == 'colabora':
                        # Activar colabora
                        if benefit.assign_colabora():
                            benefit.assign_credentials_colabora()

                    elif benefit.product_id.benefit_type == 'tarjeta_digital':
                        if benefit.digital_card_ids:
                            benefit.send_digital_cards_bearer(template)
                        else:
                            raise ValidationError(_('¡Error! No hay tarjetas digitales para generar 😔.\n\nPara solicitarlas: \n'\
                                                    '1. Active el modo edición yendo al botón EDITAR del lado superior izquierdo.\n'\
                                                    '2. Vaya a la sección de Tarjetas Digitales.\n'\
                                                    '3. Pulse la opción "Agregar línea."'))

                    #Actualizar Contacto y Empresa
                    benefit.update_contact(benefit.partner_id)
                    if benefit.parent_id:
                        benefit.update_company(benefit)

                    benefit.write({'state': 'done', 'delivery_date': datetime.now()})
                else:
                    raise ValidationError(_('La empresa seleccionada no tiene email.'))
                self.env.cr.commit()

        return {'type': 'ir.actions.act_window_close'}

    def action_re_done(self):
        """
        forward email kit notification
        <important> this function don't assign codes, colabora or analytica.</important>
        """
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if benefit_application.partner_id.contact_email:
                access_link = partner._notify_get_action_link('view')

                if benefit_application.product_id.benefit_type == 'codigos':
                    #para sellers éxito se envía otro kit de bienvenida
                    if benefit_application.is_seller:
                        template = self.env.ref('rvc.mail_template_welcome_kit_rvc_seller')
                    else:
                        template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                elif benefit_application.product_id.benefit_type == 'colabora':
                    template = self.env.ref('rvc.mail_template_welcome_kit_colabora_rvc')
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    template = self.env.ref('rvc.mail_template_welcome_kit_digital_card_rvc')

                # adjuntar la OM al kit de bienvenida si no se postuló desde Odoo
                if benefit_application.origin != 'odoo':
                    #se usa para eliminar los adjuntos de la plantilla de correo
                    template.attachment_ids = [(5,)]
                    template= benefit_application.create_OM_attachment(template)
                else:
                    template.attachment_ids = False

                try:
                    # Se envía kit de bienvenida
                    # excepto si es tarjeta digital, en ese caso el beneficio se activa primero y luego enviamos kit con 
                    # la funcion send_digital_cards_bearer()
                    if benefit_application.product_id.benefit_type != 'tarjeta_digital':
                        template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)
                        #se usa para eliminar los adjuntos de la plantilla de correo
                        template.attachment_ids = [(5,)]
                    benefit_application.message_post(body=_(\
                    'Se <strong>REENVIÓ</strong></u> el kit de bienvenida del beneficio.'))
                except Exception as e:
                    benefit_application.message_post(body=_(\
                        'No se pudo <strong>REENVIAR</strong></u> el kit de bienvenida del beneficio %s. Error: %s' % str(benefit_application.product_id.benefit_type), str(e)))
                    

                #Enviando tarjetas
                if benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    benefit_application.send_digital_cards_bearer(template)
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))

        return {'type': 'ir.actions.act_window_close'}

    def action_rejected(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            benefit_application.write({'state': 'rejected', 'rejection_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}

    def re_assign_credentials(self):
        for rec in self:
            if rec.email_credentials is not False:
                logging.info(rec.email_credentials)
                match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(rec.email_credentials).lower())

                if match is None:
                    raise UserError(f"El email '{str(rec.email_credentials).lower()}' NO es válido. Por favor verifíquelo.")

                context = dict(self._context or {})
                active_id = context.get('active_ids', False)
                benefit_application = self.env['benefit.application'].browse(active_id)
                if benefit_application:
                    if benefit_application.product_id.benefit_type == 'codigos':
                        benefit_application.assign_credentials_gs1codes(re_assign=True, re_assign_email=rec.email_credentials)
                    if benefit_application.product_id.benefit_type == 'colabora':
                        benefit_application.assign_credentials_colabora(re_assign=True, re_assign_email=rec.email_credentials)
        return True

    def action_application_done(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            for benefit in benefit_application:
                benefit.write({'state': 'done', 'date_done_cons': self.date_done_cons})
        return {'type': 'ir.actions.act_window_close'}

    def action_application_confirm(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            for benefit in benefit_application:
                benefit.write({'state': 'confirm'})
        return {'type': 'ir.actions.act_window_close'}