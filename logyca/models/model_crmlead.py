# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo CRM_LEAD / OPORTUNIDADES-------------------------------#

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    #AREA Y CARGO
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', track_visibility='onchange')
    x_contact_area = fields.Many2one('logyca.areas', string='Área', track_visibility='onchange')
    
    @api.onchange('partner_id')
    def _onchange_partner_id_jobposition(self):
        
        partner = self.env['res.partner'].browse(self.partner_id.id)
        
        values = {
                'x_contact_area': partner.x_contact_area ,
                'x_contact_job_title': partner.x_contact_job_title ,
            }
        self.update(values)

    
    
