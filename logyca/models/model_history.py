# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class x_history_partner_notes(models.Model):
    _name = 'logyca.history_partner_notes'
    _description = 'Información historia de salesforce NOTAS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    
class x_history_partner_emails(models.Model):
    _name = 'logyca.history_partner_emails'
    _description = 'Información historia de salesforce EMAILS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    from_address = fields.Text(string='Desde')    
    to_address = fields.Text(string='Para')    
    cc_Address = fields.Text(string='Cc')    
    bcc_Address = fields.Text(string='Cco')    

class x_history_partner_opportunity(models.Model):
    _name = 'logyca.history_partner_opportunity'
    _description = 'Información historia de salesforce OPORTUNIDADES'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    activity_date = fields.Datetime(string='Fecha creación', required=True)
    name = fields.Char(string='Nombre', size=50, required=True)
    description = fields.Text(string='Descripción') 
    state = fields.Char(string='Estado', size=50, required=True)   
    amount = fields.Integer(string='Monto')
    probability = fields.Integer(string='Probabilidad')
    expected_revenue = fields.Integer(string='Ingresos esperados')
    opportunity_quantity = fields.Integer(string='Cantidad')
    close_date = fields.Datetime(string='Fecha finalización')
    lead_source = fields.Char(string='Origen', size=50, required=True)
    x_history_partner_services = fields.One2many('logyca.history_partner_services', 'opportunity_id', string = 'Servicios')

class x_history_partner_services(models.Model):
    _name = 'logyca.history_partner_services'
    _description = 'Información historia de salesforce SERVICIOS x OPORTUNIDAD'

    opportunity_id = fields.Many2one('logyca.history_partner_opportunity',string='Oportunidad', required=True, ondelete='cascade')
    service = fields.Text(string='Servicio', required=True)
    service_date = fields.Datetime(string='Fecha')
    quantity = fields.Integer(string='Cantidad')
    unit_price = fields.Integer(string='Precio unitario')
    total_price = fields.Integer(string='Precio total')
    date_initial = fields.Datetime(string='Fecha inicial')
    date_finally = fields.Datetime(string='Fecha final')
 