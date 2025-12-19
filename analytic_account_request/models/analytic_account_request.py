# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import secrets

class AnalyticAccountRequest(models.Model):
    _name = 'analytic.account.request'
    _description = 'Solicitud de Cuenta Analítica'
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
    partner_id = fields.Many2one(
        'res.partner',
        string='Solicitado Por',
        required=True,
        domain="[('id', 'in', available_partner_ids)]",
        tracking=True
    )
    
    available_partner_ids = fields.Many2many(
        'res.partner',
        compute='_compute_available_partners',
        string='Partners Disponibles'
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Empleado',
        compute='_compute_employee_data',
        store=True,
        tracking=True
    )
    
    email = fields.Char(
        string='Correo Electrónico',
        compute='_compute_employee_data',
        store=True,
        tracking=True
    )
    
    # Datos de la cuenta analítica
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    plan_id = fields.Many2one(
        'account.analytic.plan',
        string='Línea de Negocio',
        required=True,
        tracking=True
    )
    
    available_plan_ids = fields.Many2many(
        'account.analytic.plan',
        compute='_compute_available_plans',
        string='Planes Disponibles'
    )
    
    analytic_account_name = fields.Char(
        string='Nombre de Cuenta Analítica',
        required=True,
        tracking=True
    )
    
    observations = fields.Text(
        string='Observaciones'
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
    
    # Cuenta analítica creada
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica',
        readonly=True,
        tracking=True
    )
    
    # Campo activo
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    @api.depends('company_id')
    def _compute_available_plans(self):
        """
        Calcula los planes analíticos que tienen cuentas analíticas de la compañía seleccionada
        """
        for record in self:
            if record.company_id:
                # Buscar cuentas analíticas de la compañía
                analytic_accounts = self.env['account.analytic.account'].search([
                    ('company_id', '=', record.company_id.id)
                ])
                
                # Obtener los planes de esas cuentas analíticas
                plan_ids = analytic_accounts.mapped('plan_id').ids
                
                record.available_plan_ids = [(6, 0, plan_ids)]
            else:
                record.available_plan_ids = [(6, 0, [])]
    
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
    
    @api.depends('partner_id')
    def _compute_employee_data(self):
        """
        Obtiene el empleado y email asociado al partner seleccionado
        """
        for record in self:
            if record.partner_id:
                # Buscar el empleado que tiene este partner como work_contact_id
                employee = self.env['hr.employee'].search([
                    ('work_contact_id', '=', record.partner_id.id)
                ], limit=1)
                
                record.employee_id = employee.id if employee else False
                record.email = employee.work_email if employee else ''
            else:
                record.employee_id = False
                record.email = ''
    
    @api.model
    def create(self, vals):
        """
        Override create para generar la secuencia del nombre
        """
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('analytic.account.request') or 'Nuevo'
        return super(AnalyticAccountRequest, self).create(vals)
    
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
            'res_model': 'analytic.account.request.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id,
            }
        }
    
    def action_create_analytic_account(self):
        """
        Crea la cuenta analítica basada en la solicitud
        """
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_('Solo se pueden crear cuentas analíticas de solicitudes aprobadas.'))
        
        if self.analytic_account_id:
            raise UserError(_('Esta solicitud ya tiene una cuenta analítica creada.'))
        
        # Crear la cuenta analítica
        analytic_account = self.env['account.analytic.account'].create({
            'name': self.analytic_account_name,
            'plan_id': self.plan_id.id,
            'company_id': self.company_id.id,
        })
        
        self.write({
            'analytic_account_id': analytic_account.id,
            'state': 'done'
        })
        
        # Enviar notificación al solicitante
        self.send_completion_notification()
        
        return {
            'name': _('Cuenta Analítica Creada'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.account',
            'res_id': analytic_account.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def send_approval_notification(self):
        """
        Envía notificación por email a los usuarios del grupo de aprobadores
        """
        self.ensure_one()
        
        # Buscar el grupo de aprobadores (se debe crear en security)
        approver_group = self.env.ref('analytic_account_request.group_analytic_account_approver', raise_if_not_found=False)
        
        if approver_group and approver_group.users:
            # Obtener emails de los usuarios del grupo
            approver_emails = [user.email for user in approver_group.users if user.email]
            
            if approver_emails:
                template = self.env.ref('analytic_account_request.email_template_request_approval', raise_if_not_found=False)
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
                            'name': 'Analytic Account Request Notification',
                            'type': 'server',
                            'level': 'info',
                            'message': f'Notificación enviada a aprobadores: {email_to}',
                            'path': 'analytic.account.request',
                            'func': 'send_approval_notification',
                            'line': '0',
                        })
                        
                        return True
                    except Exception as e:
                        # Log del error
                        self.env['ir.logging'].sudo().create({
                            'name': 'Request Approval Notification Error',
                            'type': 'server',
                            'level': 'error',
                            'message': f'Error enviando notificación: {str(e)}',
                            'path': 'analytic.account.request',
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
        
        if self.email:
            template = self.env.ref('analytic_account_request.email_template_submission_confirmation', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Submission Confirmation Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando confirmación: {str(e)}',
                        'path': 'analytic.account.request',
                        'func': 'send_submission_confirmation',
                        'line': '0',
                    })
        
        return False
    
    def send_completion_notification(self):
        """
        Envía notificación al solicitante cuando la cuenta ha sido creada
        """
        self.ensure_one()
        
        if self.email:
            template = self.env.ref('analytic_account_request.email_template_completion', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Completion Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de completación: {str(e)}',
                        'path': 'analytic.account.request',
                        'func': 'send_completion_notification',
                        'line': '0',
                    })
        
        return False
    
    def send_cancellation_notification(self):
        """
        Envía notificación al solicitante cuando la solicitud es cancelada
        """
        self.ensure_one()
        
        if self.email:
            template = self.env.ref('analytic_account_request.email_template_cancellation', raise_if_not_found=False)
            if template:
                try:
                    template.send_mail(
                        self.id,
                        force_send=True,
                        email_values={
                            'email_to': self.email,
                        }
                    )
                    return True
                except Exception as e:
                    # Log del error
                    self.env['ir.logging'].sudo().create({
                        'name': 'Cancellation Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de cancelación: {str(e)}',
                        'path': 'analytic.account.request',
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
        return f"{base_url}/web#id={self.id}&view_type=form&model=analytic.account.request"
    
    def get_analytic_account_url(self):
        """
        Retorna la URL directa para ver la cuenta analítica en Odoo
        """
        self.ensure_one()
        if self.analytic_account_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return f"{base_url}/web#id={self.analytic_account_id.id}&view_type=form&model=account.analytic.account"
        return ""


class AnalyticAccountRequestCancelWizard(models.TransientModel):
    _name = 'analytic.account.request.cancel.wizard'
    _description = 'Wizard para Cancelar Solicitud'
    
    request_id = fields.Many2one(
        'analytic.account.request',
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
