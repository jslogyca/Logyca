# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
import logging
import datetime
_logger = logging.getLogger(__name__)

#-------------------------Modelo para Crear alertas------------------------------# // Debe existir una acción planificada para ejecutarlo

class xCustomAlerts(models.Model):
    _name = 'logyca.custom_alerts'
    _description = 'Alertas personalizadas'

    name = fields.Char(string='Nombre alerta', required=True)
    description = fields.Text(string='Descripción')    
    active = fields.Boolean(string='Activa',default=True)
    model_id = fields.Many2one('ir.model', string='Modelo', required=True)
    model_name = fields.Char(related='model_id.model', string='Model Name', readonly=True, store=True)
    action_domain = fields.Char(string='Condiciones a cumplir')
    model_fields = fields.Many2many('ir.model.fields', domain="[('model_id', '=', model_id)]",string='Campos que contienen la información para la alerta')
    txt_model_fields = fields.Text(string='Nemotecnia de los campos en el cuerpo del correo', compute='_compute_txt_model_fields', store=False)
    model_field_email = fields.Many2one('ir.model.fields', domain="[('model_id', '=', model_id)]",string='Campo de correos destinatarios')
    subject = fields.Char(string='Asunto Email')
    body = fields.Text(string='Contenido Email')
    email_from = fields.Char(string='Enviado desde', required=True,default=lambda self: self.env['mail.message']._get_default_from())
    mail_server_id = fields.Many2one('ir.mail_server', string='Servidor de correo')
        
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result
    
    #Campos para el cuerpo del correo
    @api.depends('model_fields')
    def _compute_txt_model_fields(self):
        text = ''
        for field in self.model_fields:
            name_field = field.name
            name_public_field = field.field_description
            text = text + 'Para el campo '+name_public_field+' digitar %('+name_field+')s \n'
        
        self.txt_model_fields = text
            
    
    #Enviar correo
    def send_alert(self):        
        for record in self:
            #Crear objeto del modelo de la alerta
            domain = safe_eval(record.action_domain)
            name_obj = record.model_name            
            obj_alert = self.env[name_obj].search(domain)
            
            #Recorrer obj de la alerta
            for obj in obj_alert:
                #Obtener email remitente
                email_from = record.email_from
                #Obtener email destinatario
                field_email = record.model_field_email.name
                #emails = list(set([obj[field_email]]))                
                emails = list(set(['lbuitron@logyca.com']))                
                
                #Obtener asunto:
                subject = _("%s" % record.subject)
                #Obtener body del correo
                content = record.body
                for field in self.model_fields:
                    name_field = field.name
                    val_field = ''
                    try: 
                        val_field = obj[name_field].display_name
                    except:
                        val_field = obj[name_field]
                        
                    content = content.replace('%('+name_field+')s', str(val_field))
                    
                #raise ValidationError(_(content)) 
                
                #Construir correo
                email = self.env['ir.mail_server'].build_email(
                        email_from=email_from,
                        email_to=emails,
                        subject=subject, 
                        body=content,
                )
                #raise ValidationError(_(email)) 
                #Enviar correo
                self.env['ir.mail_server'].send_email(email)
            
    
