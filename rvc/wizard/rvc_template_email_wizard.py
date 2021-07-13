# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class RVCTemplateEmailWizard(models.TransientModel):
    _name = "rvc.template.email.wizard"


    note_deactive = fields.Text(string='Note deactive')


    def action_reason_desactive(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        product_benef = self.env['product.benef'].browse(active_id)
        print('/////////////////////////', active_id, product_benef)
        if product_benef:
            partner=self.env['res.partner'].search([('id','=',product_benef.partner_id.partner_id.id)])
            print('/////////////////////////')
            if partner.email:
                print('///////////////////////// 1111111', partner)
                access_link = partner._notify_get_action_link('view')
                print('///////////////////////// 22222222222', access_link)
                template = self.env.ref('rvc.mail_template_deactivated_partner_benef')
                print('///////////////////////// 333333333333', template)
                template.with_context(url=access_link).send_mail(product_benef.id, force_send=True)
            product_benef.write({'state': 'notified'})
        return {'type': 'ir.actions.act_window_close'}

#