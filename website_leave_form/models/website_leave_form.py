# -*- coding: utf-8 -*-
from odoo import api, http, fields, models, _
from odoo.http import request
from datetime import datetime

class WebsiteLeaveForm(models.Model):
    _name = 'website.leave.form'
    _description = 'Formulario Web de Ausencias'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Nombre Completo', required=True)
    email = fields.Char('Email', required=True)
    employee_id = fields.Many2one('hr.employee', 'Empleado')
    holiday_status_id = fields.Many2one('hr.leave.type', 'Tipo de Ausencia', required=True)
    approver_id = fields.Many2one('res.partner', 'Aprobador', required=True, 
                                   domain="[('id', 'in', available_approver_ids)]")
    available_approver_ids = fields.Many2many('res.partner', 
                                               compute='_compute_available_approvers',
                                               string='Aprobadores Disponibles')
    date_from = fields.Datetime('Fecha Inicio', required=True)
    date_to = fields.Datetime('Fecha Fin', required=True)
    request_date = fields.Date('Fecha de Solicitud', default=fields.Date.context_today, required=True)
    notes = fields.Text('Notas')
    attachment_ids = fields.Many2many('ir.attachment', 'website_leave_attachment_rel', 
                                      'leave_id', 'attachment_id', string='Documentos Adjuntos')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('submitted', 'Enviado'),
        ('error', 'Error'),
    ], default='draft', string='Estado', tracking=True)
    leave_id = fields.Many2one('hr.leave', 'Ausencia Creada', readonly=True)
    active = fields.Boolean('Activo', default=True)

    @api.depends('employee_id')
    def _compute_available_approvers(self):
        """
        Calcula los aprobadores disponibles basándose en el parent_id del empleado
        Solo trae el work_contact_id como aprobador (no sus contactos relacionados)
        """
        for record in self:
            approver_ids = []
            if record.employee_id and record.employee_id.parent_id:
                # Obtener el partner relacionado al parent_id del empleado
                parent_partner = record.employee_id.parent_id
                
                # Solo usar work_contact_id como aprobador
                if parent_partner.work_contact_id:
                    main_contact = parent_partner.work_contact_id
                    related_partners = self.env['res.partner'].search([
                        ('id', '=', main_contact.id)
                    ])
                    approver_ids = related_partners.ids
                # Si no tiene work_contact_id, no hay aprobadores
            
            record.available_approver_ids = [(6, 0, approver_ids)]
    
    def get_leave_url(self):
        """
        Retorna la URL directa para ver la ausencia en Odoo
        """
        self.ensure_one()
        if self.leave_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return f"{base_url}/web#id={self.leave_id.id}&view_type=form&model=hr.leave"
        return ""
    
    def get_base_url(self):
        """
        Retorna la URL base del sistema
        """
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')
    
    def send_approval_notification(self):
        """
        Envía notificación de aprobación al aprobador
        Puede ser llamado manualmente si se necesita reenviar
        """
        self.ensure_one()
        if self.approver_id and self.approver_id.email:
            template = self.env.ref('website_leave_form.email_template_leave_approval', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.approver_id.email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Leave Approval Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación: {str(e)}',
                        'path': 'website.leave.form',
                        'func': 'send_approval_notification',
                        'line': '0',
                    })
                    return False
        return False
