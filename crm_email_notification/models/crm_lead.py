# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = ['crm.lead']

    @api.model
    def create(self, vals):
        lead = super(CrmLead, self).create(vals)
        email = self.env['ir.config_parameter'].sudo().get_param('email_crm_notification')
        try:
            self.env['mail.mail'].sudo().create({
                'body_html': vals['description'],
                'subject': 'CRM ODOO Re: %s' % vals['name'],
                'email_from': vals['email_from'],
                'email_to': email,
                'auto_delete': True,
            }).send()
        except:
            pass

        return lead