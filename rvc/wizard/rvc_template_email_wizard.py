# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
from ..models.rvc_activations import RvcActivations
from markupsafe import Markup
import re
import logging
import base64


class RVCTemplateEmailWizard(models.TransientModel):
    _name = "rvc.template.email.wizard"
    _description = 'RVC Template Email Wizard'
    _rec_name = 'id'

    note_deactive = fields.Text(string='Nota Adicional')
    email_credentials = fields.Char(string="Email Credenciales")
    date_done_cons = fields.Date(string='Date Solución', default=fields.Date.context_today)
    
    def action_notify(self):
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if partner and benefit_application.contact_email:

                # Notify Identification Rights
                if benefit_application.product_id.code == '01':
                    access_link = partner._notify_get_action_link('view')
                    template = self.env.ref('rvc.mail_template_notify_benefit_codes')
                    subject = "Beneficio Derechos de Identificación"

                    email_values = {'subject': subject}
                    self._send_mail_with_attachment(
                        template=template,
                        record=benefit_application,
                        email_values=email_values,
                        report_ref='rvc.action_report_rvc',
                        attachment_name_template='Oferta_Mercantil_RVC_{partner_vat}.pdf',
                        access_link=access_link,
                        require_attachment=True
                    )

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
        print('TARJETA')
        context = dict(self._context or {})
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            if benefit_application.product_id.benefit_type == 'crece_mype':
                benefit_application._send_assing_crece_mype()
                benefit_application._get_employe(benefit_application.email_employee)
            else:
                benefit_application.message_post(
                    body=Markup(
                        _(
                            '%s <u><strong>ACEPTÓ</strong></u> el beneficio.'
                        ) % str(benefit_application.partner_id.partner_id.name)
                    ),
                    subtype_xmlid='mail.mt_comment'
                )

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
            if benefit_application.send_kit_with_no_benefit:
                benefit_application.message_post(body=_(\
                    '✅ Se entregó el beneficio RVC correctamente.'))
                return benefit_application.write({'state': 'done', 'delivery_date': datetime.now()})
            contact_email = benefit_application.partner_id.contact_email
            if contact_email:
                if benefit_application.product_id.benefit_type == 'codigos':
                    activated = self.env['rvc.activations'].activate_gs1_codes(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de Códigos GS1.'))
                elif benefit_application.product_id.benefit_type == 'colabora':
                    activated = self.env['rvc.activations'].activate_logyca_colabora(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de la plataforma LOGYCA / COLABORA.'))
                    else:
                        benefit_application.message_post(body=_(\
                            '🚫 No se pudo <strong>solicitar la activación</strong></u> de la plataforma LOGYCA / COLABORA.'))
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    if benefit_application.digital_card_ids:
                        activated = self.env['rvc.activations'].activate_digital_cards(benefit_application)
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
                match = re.match(r'^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(rec.email_credentials).lower())

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

    def _generate_and_attach_report(self, report_ref, record, attachment_name_template=None):
        """
        Function to generate a PDF report and create an attachment
        """
        try:
            # Ensure we have a single record
            record.ensure_one()

            # Get the report action
            report_action = self.env.ref(report_ref)

            # Verify report exists
            if not report_action.exists():
                logging.error("Report does not exist: %s", report_ref)
                return False

            # Generate PDF
            pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf(
                report_action, [record.id]
            )

            if not pdf_content:
                logging.error("PDF content is empty for report %s", report_ref)
                return False

            # Encode in base64
            pdf_base64 = base64.b64encode(pdf_content)

            # Generate safe file name
            if attachment_name_template:
                try:
                    partner_vat = record.partner_id.partner_id.vat or 'Unknown'
                    # Clean VAT for filesystem compatibility
                    partner_vat = re.sub(r'[^\w\s-]', '', str(partner_vat)).strip()
                    partner_vat = re.sub(r'[-\s]+', '_', partner_vat)

                    attachment_name = attachment_name_template.format(
                        partner_vat=partner_vat,
                        record_id=record.id,
                        report_name=report_action.name or 'Report'
                    )
                except Exception as name_error:
                    logging.warning("Error formatting attachment name: %s", str(name_error))
                    attachment_name = f'Report_{record.id}.pdf'
            else:
                attachment_name = f'{report_action.name or "Report"}_{record.id}.pdf'

            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': attachment_name,
                'type': 'binary',
                'datas': pdf_base64,
                'res_model': record._name,
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })

            logging.info("Successfully generated PDF attachment: %s", attachment_name)
            return attachment

        except Exception as e:
            logging.error("Error generating PDF report %s: %s", report_ref, str(e))
            return False

    def _send_mail_with_attachment(self, template, record, email_values, report_ref=None,
                                   attachment_name_template=None, access_link=None,
                                   require_attachment=False):
        """
        Reusable function to send email with optional/required attachment

        Args:
            template (mail.template): Email template to send
            record (recordset): Related record
            email_values (dict): Additional values for the email
            report_ref (str): Reference of the report to attach (optional)
            attachment_name_template (str): Template for file name (optional)
            access_link (str): Access link for context (optional)
            require_attachment (bool): If True, fails if attachment cannot be generated

        Returns:
            bool: True if sent successfully

        Raises:
            UserError: If require_attachment=True and attachment generation fails
        """
        try:
            # Prepare context
            context = {}
            if access_link:
                context['url'] = access_link

            # If report is required, try to generate attachment
            if report_ref:
                attachment = self._generate_and_attach_report(
                    report_ref,
                    record,
                    attachment_name_template
                )

                if attachment:
                    # Add attachment to email_values
                    if 'attachment_ids' not in email_values:
                        email_values['attachment_ids'] = []
                    email_values['attachment_ids'].append((4, attachment.id))
                elif require_attachment:
                    # If attachment is required and generation failed, raise error
                    attachment_name = attachment_name_template or 'PDF report'
                    if attachment_name_template:
                        attachment_name = attachment_name_template.format(
                            partner_name=record.partner_id.partner_id.name,
                            record_id=record.id,
                            report_name='report'
                        )
                    raise UserError(_(
                        'Could not send email because the required attachment could not be generated: %s. '
                        'Please verify that the report is correctly configured.' % attachment_name
                    ))

            # Send email
            template.with_context(**context).send_mail(
                record.id,
                force_send=False,
                email_values=email_values
            )

            return True

        except UserError:
            # Re-raise UserError so it's shown to the user
            raise
        except Exception as e:
            logging.error("Error sending email with template %s: %s", template.id, str(e))
            if require_attachment and report_ref:
                # If attachment is required and there's an error, raise specific UserError
                raise UserError(_(
                    'Could not send email due to a system error: %s' % str(e)
                ))
            return False

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