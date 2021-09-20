# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime

class RVCTemplateEmailWizard(models.TransientModel):
    _name = "rvc.template.email.wizard"
    _rec_name = 'id'


    note_deactive = fields.Text(string='Nota Adicional')


    def action_reason_desactive(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if partner and benefit_application.contact_email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_deactivated_partner_benef')
                template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)
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
            benefit_application.write({'state': 'confirm', 'acceptance_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}

    def action_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefit_application = self.env['benefit.application'].browse(active_id)
        if benefit_application:
            partner=self.env['res.partner'].search([('id','=',benefit_application.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                template.with_context(url=access_link).send_mail(benefit_application.id, force_send=True)

                if not benefit_application.gln:
                    # si no tiene GLN, asignamos uno.
                    benefit_application.assignate_gln_code()

                # Asignar beneficio de códigos de identificación
                if benefit_application.assign_identification_codes():
                    benefit_application.assign_credentials_for_codes()

                # Actualizar Contacto y Empresa
                benefit_application.update_contact(benefit_application.partner_id)
                if benefit_application.parent_id:
                    benefit_application.update_company(benefit_application)

                # Agregar tipo de vinculacion al tercero
                benefit_application.add_vinculation_partner()

                benefit_application.write({'state': 'done'})
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
