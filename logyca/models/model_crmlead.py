# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

#---------------------------Modelo CRM_LEAD / OPORTUNIDADES-------------------------------#

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    #AREA Y CARGO
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', track_visibility='onchange')
    x_contact_area = fields.Many2one('logyca.areas', string='Área', track_visibility='onchange')
    
    
