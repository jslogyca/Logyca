# -*- coding: utf-8 -*-
from odoo import api, http, fields, models, _
from odoo.http import request
from datetime import datetime
import secrets
import hashlib

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
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
        ('error', 'Error'),
    ], default='draft', string='Estado', tracking=True)
    leave_id = fields.Many2one('hr.leave', 'Ausencia Creada', readonly=True)
    active = fields.Boolean('Activo', default=True)
    
    # Campos para aprobación por email
    approval_token = fields.Char('Token de Aprobación', copy=False, readonly=True)
    approval_date = fields.Datetime('Fecha de Aprobación', readonly=True)
    approved_by_email = fields.Boolean('Aprobado por Email', default=False, readonly=True)

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
    
    def generate_approval_token(self):
        """
        Genera un token único para aprobación por email
        """
        import secrets
        self.ensure_one()
        if not self.approval_token:
            self.approval_token = secrets.token_urlsafe(32)
        return self.approval_token
    
    def get_approval_url(self, action='approve'):
        """
        Retorna la URL para aprobar o rechazar desde el email
        action: 'approve' o 'reject'
        """
        self.ensure_one()
        if not self.approval_token:
            self.generate_approval_token()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/ausencias/approve/{self.id}/{self.approval_token}/{action}"
    
    def approve_by_token(self, token):
        """
        Aprueba la ausencia usando el token de aprobación
        Retorna True si se aprobó exitosamente
        """
        self.ensure_one()
        
        # Verificar token
        if not self.approval_token or self.approval_token != token:
            return {'success': False, 'message': 'Token inválido o expirado'}
        
        # Verificar que no esté ya aprobada o rechazada
        if self.state in ['approved', 'rejected']:
            return {'success': False, 'message': f'Esta solicitud ya fue {self.state}'}
        
        try:
            # Aprobar la ausencia en hr.leave
            if self.leave_id:
                self.leave_id.sudo().action_approve()
            
            # Actualizar estado
            self.write({
                'state': 'approved',
                'approval_date': fields.Datetime.now(),
                'approved_by_email': True,
            })
            
            # Enviar email de confirmación
            self.send_approval_confirmation_email(action='approved')
            
            return {'success': True, 'message': 'Ausencia aprobada exitosamente'}
            
        except Exception as e:
            # Log del error
            self.env['ir.logging'].sudo().create({
                'name': 'Leave Approval Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error aprobando ausencia: {str(e)}',
                'path': 'website.leave.form',
                'func': 'approve_by_token',
                'line': '0',
            })
            return {'success': False, 'message': f'Error al aprobar: {str(e)}'}
    
    def reject_by_token(self, token):
        """
        Rechaza la ausencia usando el token de aprobación
        Retorna True si se rechazó exitosamente
        """
        self.ensure_one()
        
        # Verificar token
        if not self.approval_token or self.approval_token != token:
            return {'success': False, 'message': 'Token inválido o expirado'}
        
        # Verificar que no esté ya aprobada o rechazada
        if self.state in ['approved', 'rejected']:
            return {'success': False, 'message': f'Esta solicitud ya fue {self.state}'}
        
        try:
            # Rechazar la ausencia en hr.leave
            if self.leave_id:
                self.leave_id.sudo().action_refuse()
            
            # Actualizar estado
            self.write({
                'state': 'rejected',
                'approval_date': fields.Datetime.now(),
                'approved_by_email': True,
            })
            
            # Enviar email de confirmación
            self.send_approval_confirmation_email(action='rejected')
            
            return {'success': True, 'message': 'Ausencia rechazada'}
            
        except Exception as e:
            # Log del error
            self.env['ir.logging'].sudo().create({
                'name': 'Leave Rejection Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error rechazando ausencia: {str(e)}',
                'path': 'website.leave.form',
                'func': 'reject_by_token',
                'line': '0',
            })
            return {'success': False, 'message': f'Error al rechazar: {str(e)}'}
    
    def send_approval_confirmation_email(self, action='approved'):
        """
        Envía email de confirmación al empleado y aprobador
        action: 'approved' o 'rejected'
        """
        self.ensure_one()
        
        template_name = 'email_template_leave_approved' if action == 'approved' else 'email_template_leave_rejected'
        template = self.env.ref(f'website_leave_form.{template_name}', raise_if_not_found=False)
        
        if template:
            try:
                # Email al empleado y aprobador (con copia)
                email_to = self.email
                email_cc = self.approver_id.email if self.approver_id and self.approver_id.email else ''
                
                template.sudo().send_mail(
                    self.id,
                    force_send=True,
                    email_values={
                        'email_to': email_to,
                        'email_cc': email_cc,
                    }
                )
                
                # Log de éxito
                self.env['ir.logging'].sudo().create({
                    'name': f'Leave {action.title()} Email Sent',
                    'type': 'server',
                    'level': 'info',
                    'message': f'Email de confirmación enviado a {email_to} con copia a {email_cc}',
                    'path': 'website.leave.form',
                    'func': 'send_approval_confirmation_email',
                    'line': '0',
                })
                
            except Exception as e:
                # Log del error
                self.env['ir.logging'].sudo().create({
                    'name': 'Confirmation Email Error',
                    'type': 'server',
                    'level': 'error',
                    'message': f'Error enviando email de confirmación: {str(e)}',
                    'path': 'website.leave.form',
                    'func': 'send_approval_confirmation_email',
                    'line': '0',
                })
