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
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            partner=self.env['res.partner'].search([('id','=',benefits_admon.partner_id.partner_id.id)])
            if partner and benefits_admon.contact_email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_deactivated_partner_benef')
                template.with_context(url=access_link).send_mail(benefits_admon.id, force_send=True)
                benefits_admon.write({'state': 'notified', 'notification_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}


    def action_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            benefits_admon.message_post(body=_(\
                    '%s <u><strong>ACEPTÓ</strong></u> el beneficio.' % str(benefits_admon.partner_id.partner_id.name)))
            benefits_admon.write({'state': 'confirm', 'acceptance_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}

    def action_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            partner=self.env['res.partner'].search([('id','=',benefits_admon.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                template.with_context(url=access_link).send_mail(benefits_admon.id, force_send=True)

                if not benefits_admon.gln:
                    # si no tiene GLN, asignamos uno.
                    benefits_admon.assignate_gln_code()

                # Asignar beneficio de códigos de identificación
                if benefits_admon.assign_identification_codes():
                    benefits_admon.assign_credentials_for_codes()

                # Actualizar Contacto y Empresa
                benefits_admon.update_contact(benefits_admon.partner_id)
                if benefits_admon.parent_id:
                    benefits_admon.update_company(benefits_admon)

                benefits_admon.write({'state': 'done'})
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))
            
        return {'type': 'ir.actions.act_window_close'}


    def action_rejected(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            benefits_admon.write({'state': 'rejected', 'rejection_date': datetime.now()})
        return {'type': 'ir.actions.act_window_close'}
