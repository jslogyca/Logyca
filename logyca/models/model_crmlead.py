# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo CRM_LEAD / OPORTUNIDADES-------------------------------#

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    #AREA Y CARGO
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', track_visibility='onchange')
    x_contact_area = fields.Many2one('logyca.areas', string='Área', track_visibility='onchange')
    
    def _onchange_partner_id_values(self, partner_id):
        """ returns the new values when partner_id has changed """
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)

            partner_name = partner.parent_id.name
            if not partner_name and partner.is_company:
                partner_name = partner.name

            return {
                'partner_name': partner_name,
                'contact_name': partner.name if not partner.is_company else False,
                'title': partner.title.id,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'state_id': partner.state_id.id,
                'country_id': partner.country_id.id,
                'email_from': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'zip': partner.zip,
                'function': partner.function,
                'website': partner.website,
                'x_contact_area': partner.x_contact_area ,
                'x_contact_job_title': partner.x_contact_job_title ,
            }
        return {}

    @api.depends('partner_id')
    def _onchange_partner_id(self):
        values = self._onchange_partner_id_values(super.partner_id.id if super.partner_id else False)
        self.update(values)

    
    
