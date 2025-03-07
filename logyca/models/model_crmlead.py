# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

#---------------------------Modelo CRM_LEAD / OPORTUNIDADES-------------------------------#

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    #AREA Y CARGO
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', tracking=True)
    x_contact_area = fields.Many2one('logyca.areas', string='Área', tracking=True)
    x_analytic_account_id =  fields.Many2one('account.analytic.account', string ='Cuenta Análitica', tracking=True)
    x_analytic_account_family = fields.Many2one( string ='Familia Análitica', related = 'x_analytic_account_id.group_id', readonly = True, store = True )
    x_analytic_account_line = fields.Many2one( string ='Línea Análitica', related = 'x_analytic_account_family.parent_id', readonly = True, store = True )
    
    @api.onchange('partner_id')
    def _onchange_partner_id_jobposition(self):
        
        partner = self.env['res.partner'].browse(self.partner_id.id)
        
        values = {
                'x_contact_area': partner.x_contact_area ,
                'x_contact_job_title': partner.x_contact_job_title ,
            }
        self.update(values)  


class CrmStage(models.Model):   
    _inherit = 'crm.stage'
    
    is_lose = fields.Boolean('¿Es la Etapa NO Ganada?')
    
