# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class CreditCardRequest(models.Model):
    _name = 'credit.card.request'
    _description = 'Solicitud de Tarjeta de Crédito'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Campos de la solicitud
    name = fields.Char(
        string='Número de Solicitud',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )
    
    request_date = fields.Date(
        string='Fecha de Solicitud',
        default=fields.Date.context_today,
        required=True,
        readonly=True,
        tracking=True
    )
    
    # Información del solicitante
    requester_partner_id = fields.Many2one(
        'res.partner',
        string='Nombre del Colaborador (Solicitante)',
        required=True,
        domain="[('id', 'in', available_partner_ids)]",
        tracking=True
    )
    
    available_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_available_partners',
        string='Partners Disponibles'
    )
    
    requester_employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado Solicitante',
        compute='_compute_requester_data',
        store=True,
        tracking=True
    )
    
    requester_email = fields.Char(
        string='Email del Solicitante',
        compute='_compute_requester_data',
        store=True,
        tracking=True
    )
    
    # Información del tarjetahabiente
    cardholder_partner_id = fields.Many2one(
        'res.partner',
        string='Nombre del Tarjetahabiente',
        required=True,
        domain="[('id', 'in', available_partner_ids)]",
        tracking=True
    )
    
    cardholder_employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado Tarjetahabiente',
        compute='_compute_cardholder_data',
        store=True,
        tracking=True
    )
    
    cardholder_identification = fields.Char(
        string='Número de Cédula Tarjetahabiente',
        required=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Organización del Tarjetahabiente',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    department_id = fields.Many2one(
        'hr.department',
        string='Equipo',
        required=True,
        domain="[('company_id', '=', company_id)]",
        tracking=True
    )
    
    job_id = fields.Many2one(
        'hr.job',
        string='Cargo del Tarjetahabiente',
        compute='_compute_cardholder_data',
        store=True,
        tracking=True
    )
    
    # Estado y aprobación
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('requested', 'Solicitado'),
        ('approved', 'Aprobado'),
        ('done', 'Terminado'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='draft', required=True, tracking=True)
    
    cancel_reason = fields.Text(
        string='Razón de Cancelación',
        tracking=True
    )
    
    # Campo activo
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    @api.depends()
    def _compute_available_partners(self):
        """
        Calcula todos los partners que están asociados a empleados (work_contact_id)
        """
        for record in self:
            # Obtener todos los empleados activos
            employees = self.env['hr.employee'].search([('active', '=', True)])
            
            # Obtener sus work_contact_id
            partner_ids = employees.mapped('work_contact_id').ids
            
            record.available_partner_ids = [(6, 0, partner_ids)]
    
    @api.depends('requester_partner_id')
    def _compute_requester_data(self):
        """
        Obtiene el empleado y email del solicitante
        """
        for record in self:
            if record.requester_partner_id:
                # Buscar el empleado que tiene este partner como work_contact_id
                employee = self.env['hr.employee'].search([
                    ('work_contact_id', '=', record.requester_partner_id.id)
                ], limit=1)
                
                record.requester_employee_id = employee.id if employee else False
                record.requester_email = employee.work_email if employee else ''
            else:
                record.requester_employee_id = False
                record.requester_email = ''
    
    @api.depends('cardholder_partner_id')
    def _compute_cardholder_data(self):
        """
        Obtiene el empleado y cargo del tarjetahabiente
        """
        for record in self:
            if record.cardholder_partner_id:
                # Buscar el empleado que tiene este partner como work_contact_id
                employee = self.env['hr.employee'].search([
                    ('work_contact_id', '=', record.cardholder_partner_id.id)
                ], limit=1)
                
                record.cardholder_employee_id = employee.id if employee else False
                record.job_id = employee.job_id.id if employee and employee.job_id else False
            else:
                record.cardholder_employee_id = False
                record.job_id = False
    
    @api.model
    def create(self, vals):
        """
        Override create para generar la secuencia del nombre
        """
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('credit.card.request') or 'Nuevo'
        return super(CreditCardRequest, self).create(vals)
    
    def action_submit(self):
        """
        Envía la solicitud y cambia el estado a 'Solicitado'
        Envía notificación a los usuarios del grupo de aprobadores
        """
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_('Solo se pueden enviar solicitudes en estado Borrador.'))
        
        self.write({'state': 'requested'})
        
        # Enviar notificación a aprobadores
        self.send_approval_notification()
        
        # Enviar confirmación al solicitante
        self.send_submission_confirmation()
        
        return True
    
    def action_approve(self):
        """
        Aprueba la solicitud
        """
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_('Solo se pueden aprobar solicitudes en estado Solicitado.'))
        
        self.write({'state': 'approved'})
        
        return True
    
    def action_done(self):
        """
        Marca la solicitud como terminada
        """
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_('Solo se pueden terminar solicitudes en estado Aprobado.'))
        
        self.write({'state': 'done'})
        
        # Enviar notificación al solicitante
        self.send_completion_notification()
        
        return True
    
    def action_cancel(self):
        """
        Abre un wizard para cancelar la solicitud con razón
        """
        self.ensure_one()
        
        if self.state not in ['requested', 'approved']:
            raise UserError(_('Solo se pueden cancelar solicitudes en estado Solicitado o Aprobado.'))
        
        # Abrir wizard para ingresar razón de cancelación
        return {
            'name': _('Cancelar Solicitud'),
            'type': 'ir.actions.act_window',
            'res_model': 'credit.card.request.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }
    
    def send_approval_notification(self):
        """
        Envía notificación por email a los usuarios del grupo de aprobadores
        """
        self.ensure_one()
        
        # Buscar el grupo de aprobadores
        approver_group = self.env.ref('analytic_account_request.group_credit_card_approver', raise_if_not_found=False)
        
        if approver_group and approver_group.users:
            # Obtener emails de los usuarios del grupo
            approver_emails = [user.email for user in approver_group.users if user.email]
            
            if approver_emails:
                template = self.env.ref('analytic_account_request.email_template_credit_card_approval', raise_if_not_found=False)
                if template:
                    try:
                        # Enviar email a todos los aprobadores
                        email_to = ','.join(approver_emails)
                        template.send_mail(
                            self.id,
                            force_send=True,
                            email_values={
                                'email_to': email_to,
                            }
                        )
                        
                        # Log de éxito
                        self.env['ir.logging'].sudo().create({
                            'name': 'Credit Card Request Notification',
                            'type': 'server',
                            'level': 'info',
                            'message': f'Notificación enviada a aprobadores: {email_to}',
                            'path': 'credit.card.request',
                            'func': 'send_approval_notification',
                            'line': '0',
                        })
                        
                        return True
                    except Exception as e:
                        # Log del error
                        self.env['ir.logging'].sudo().create({
                            'name': 'Credit Card Approval Notification Error',
                            'type': 'server',
                            'level': 'error',
                            'message': f'Error enviando notificación: {str(e)}',
                            'path': 'credit.card.request',
                            'func': 'send_approval_notification',
                            'line': '0',
                        })
                        return False
        
        return False
    
    def send_submission_confirmation(self):
        """
        Envía email de confirmación al solicitante
        """
        self.ensure_one()
        
        if self.requester_email:
            template = self.env.ref('analytic_account_request.email_template_credit_card_submission', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.requester_email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Credit Card Submission Confirmation Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando confirmación: {str(e)}',
                        'path': 'credit.card.request',
                        'func': 'send_submission_confirmation',
                        'line': '0',
                    })
        
        return False
    
    def send_completion_notification(self):
        """
        Envía notificación al solicitante cuando la solicitud está terminada
        """
        self.ensure_one()
        
        if self.requester_email:
            template = self.env.ref('analytic_account_request.email_template_credit_card_completion', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.requester_email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Credit Card Completion Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de completación: {str(e)}',
                        'path': 'credit.card.request',
                        'func': 'send_completion_notification',
                        'line': '0',
                    })
        
        return False
    
    def send_cancellation_notification(self):
        """
        Envía notificación al solicitante cuando la solicitud es cancelada
        """
        self.ensure_one()
        
        if self.requester_email:
            template = self.env.ref('analytic_account_request.email_template_credit_card_cancellation', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.requester_email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Credit Card Cancellation Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de cancelación: {str(e)}',
                        'path': 'credit.card.request',
                        'func': 'send_cancellation_notification',
                        'line': '0',
                    })
        
        return False
    
    def get_request_url(self):
        """
        Retorna la URL directa para ver la solicitud en Odoo
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return f"{base_url}/web#id={self.id}&view_type=form&model=credit.card.request"


class CreditCardRequestCancelWizard(models.TransientModel):
    _name = 'credit.card.request.cancel.wizard'
    _description = 'Wizard para Cancelar Solicitud de Tarjeta de Crédito'
    
    request_id = fields.Many2one(
        'credit.card.request',
        string='Solicitud',
        required=True
    )
    
    cancel_reason = fields.Text(
        string='Razón de Cancelación',
        required=True
    )
    
    def action_confirm_cancel(self):
        """
        Confirma la cancelación de la solicitud
        """
        self.ensure_one()
        
        self.request_id.write({
            'state': 'cancelled',
            'cancel_reason': self.cancel_reason,
        })
        
        # Enviar notificación de cancelación
        self.request_id.send_cancellation_notification()
        
        return {'type': 'ir.actions.act_window_close'}
