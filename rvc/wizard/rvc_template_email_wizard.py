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
        product_benef = self.env['product.benef'].browse(active_id)
        if product_benef:
            partner=self.env['res.partner'].search([('id','=',product_benef.partner_id.partner_id.id)])
            if partner and product_benef.email_contact:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_deactivated_partner_benef')
                template.with_context(url=access_link).send_mail(product_benef.id, force_send=True)
            product_benef.write({'state': 'notified'})
        return {'type': 'ir.actions.act_window_close'}


    def action_confirm(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        product_benef = self.env['product.benef'].browse(active_id)
        if product_benef:
            partner=self.env['res.partner'].search([('id','=',product_benef.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_aceptacion_beneficios_rvc')
                template.with_context(url=access_link).send_mail(product_benef.id, force_send=True)
            product_benef.write({'state': 'confirm'})
        return {'type': 'ir.actions.act_window_close'}


    def action_done(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        product_benef = self.env['product.benef'].browse(active_id)
        if product_benef:
            partner=self.env['res.partner'].search([('id','=',product_benef.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_kit_bienvenida_derecho_rvc')
                template.with_context(url=access_link).send_mail(product_benef.id, force_send=True)
            product_benef.write({'state': 'done'})
        return {'type': 'ir.actions.act_window_close'}


    def action_rejected(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        product_benef = self.env['product.benef'].browse(active_id)
        if product_benef:
            partner=self.env['res.partner'].search([('id','=',product_benef.partner_id.partner_id.id)])
            if partner.email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_rechazo_beneficios_rvc')
                template.with_context(url=access_link).send_mail(product_benef.id, force_send=True)
            product_benef.write({'state': 'rejected'})
        return {'type': 'ir.actions.act_window_close'}

#