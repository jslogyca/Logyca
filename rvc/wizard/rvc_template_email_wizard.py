# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


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
            benefits_admon.write({'state': 'notified'})
        return {'type': 'ir.actions.act_window_close'}


    def action_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            partner=self.env['res.partner'].search([('id','=',benefits_admon.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_aceptacion_beneficios_rvc')
                template.with_context(url=access_link).send_mail(benefits_admon.id, force_send=True)
            benefits_admon.write({'state': 'confirm'})
        return {'type': 'ir.actions.act_window_close'}


    def update_contact(self, company_id):
        type_id = self.env.ref('rvc.contact_types_rvc').id,
        self._cr.execute(''' SELECT id FROM res_partner WHERE email=%s AND is_company IS False 
                                AND parent_id=(SELECT id FROM res_partner WHERE vat=%s AND is_company IS True) ''', 
                                            (company_id.contact_email, company_id.vat))
        contact_id= self._cr.fetchone()
        if contact_id and contact_id[0]:
            self._cr.execute(''' SELECT * FROM logyca_contact_types_res_partner_rel WHERE res_partner_id=%s AND logyca_contact_types_id=%s ''', (contact_id[0], type_id))
            type_contact = self._cr.fetchone()
            if not type_contact:
                self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel 
                                        (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_id[0], type_id))
        else:
            contact_new = self.env['res.partner'].create({
                                        'name': company_id.contact_name,
                                        'street': company_id.partner_id.street,
                                        'country_id': company_id.partner_id.country_id.id,
                                        'state_id': company_id.partner_id.state_id.id,
                                        'email': company_id.contact_email,
                                        'phone': company_id.contact_phone,
                                        'vat': company_id.vat,
                                        'parent_id': company_id.partner_id.id,
                                        'x_city': company_id.partner_id.x_city.id})
            self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel 
                                    (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_new.id, type_id))
        return True

    def update_company(self, company_id):
        self._cr.execute(''' UPDATE res_partner SET x_sponsored=%s, x_flagging_company=%s WHERE id=%s ''', 
                                        (True, company_id.parent_id.partner_id.id, company_id.partner_id.partner_id.id))
        return True


    def action_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            partner=self.env['res.partner'].search([('id','=',benefits_admon.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_kit_bienvenida_derecho_rvc')
                template.with_context(url=access_link).send_mail(benefits_admon.id, force_send=True)
            benefits_admon.write({'state': 'done'})
            # Actualizar Contacto y Empresa
            self.update_contact(benefits_admon.partner_id)
            if benefits_admon.parent_id:
                self.update_company(benefits_admon)
        return {'type': 'ir.actions.act_window_close'}


    def action_rejected(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        benefits_admon = self.env['benefits.admon'].browse(active_id)
        if benefits_admon:
            partner=self.env['res.partner'].search([('id','=',benefits_admon.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_rechazo_beneficios_rvc')
                template.with_context(url=access_link).send_mail(benefits_admon.id, force_send=True)
            benefits_admon.write({'state': 'rejected'})
        return {'type': 'ir.actions.act_window_close'}

#