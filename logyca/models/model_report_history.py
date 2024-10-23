# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

class x_report_partner_history(models.TransientModel):
    _name = 'logyca.report.history_partner'
    _description = 'Consultar información Historica del Cliente'
    
    type_info_filter = fields.Selection([
                                        ('logyca.history_partner_notes', 'Notas'),
                                        ('logyca.history_partner_emails', 'Emails'),
                                        ('logyca.history_partner_opportunity', 'Oportunidades / Servicios / Facturas'),
                                        ('logyca.history_partner_case', 'Casos')        
                                    ], string='Inf. Historica a Consultar', required=True, default='logyca.history_partner_notes')    
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, domain=[('x_type_thirdparty', 'not in', [2])])
    filter_domain = fields.Char(string='Filtro')
    visible_result = fields.Boolean(string='Visible',default=False)
    #Campos a filtrar    
    x_history_partner_notes = fields.Many2many('logyca.history_partner_notes', string = 'Notas')
    x_history_partner_emails = fields.Many2many('logyca.history_partner_emails', string = 'Emails')
    x_history_partner_opportunity = fields.Many2many('logyca.history_partner_opportunity', relation='logyca_history_partner_opportunity_report_rel',string = 'Oportunidades')
    x_history_partner_case = fields.Many2many('logyca.history_partner_case', string = 'Casos')
    
    def name_get(self):
        result = []
        for record in self:    
            result.append((record.id, "Información Historica del Cliente {}".format(record.partner_id.name)))
        return result
    
    def upload_filter(self):
        for partner in self.partner_id:  
            if not self.filter_domain:
                raise ValidationError(_("No se selecciono ningún filtro, por favor verifique."))  
            
            domain = [('partner_id', '=', partner.id)] + safe_eval(self.filter_domain)
            #raise ValidationError(_(domain))  
            name_obj = self.type_info_filter            
            obj_history = self.env[name_obj].search(domain)
            
            if not obj_history:
                raise ValidationError(_("No se encontró información con los filtros seleccionados, por favor verifique."))  
                self.visible_result = False
            else:
                self.visible_result = True
                
            field_obj = ''
            if name_obj == 'logyca.history_partner_notes':
                field_obj = 'x_history_partner_notes'
            if name_obj == 'logyca.history_partner_emails':
                field_obj = 'x_history_partner_emails'
            if name_obj == 'logyca.history_partner_opportunity':
                field_obj = 'x_history_partner_opportunity'
            if name_obj == 'logyca.history_partner_case':
                field_obj = 'x_history_partner_case'
                
            for obj in obj_history:
                value_update = {
                    field_obj: [(4, obj.id, 0)]                 
                }
                self.write(value_update)    