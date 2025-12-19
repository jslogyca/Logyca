# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class AdvanceRequest(models.Model):
    _name = 'advance.request'
    _description = 'Solicitud de Anticipos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Número de Solicitud',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )
    
    # Campo 1: Autorización descuento por nómina
    payroll_discount_auth = fields.Selection([
        ('yes', 'SI'),
        ('no', 'NO')
    ], string='Autorización descuento por nómina', required=True, tracking=True,
       help='Declaro que conozco la política organizacional de manejo y legalización de anticipos de dinero por medio de la cual debo legalizar el presente anticipo a mi cargo a más tardar dentro de los tres (3) días posteriores al recibo del mismo. En caso de incumplir dichos términos, autorizo sea descontado de mi nómina el valor del presente anticipo.')
    
    # Campo 1.1: Nombre del colaborador
    partner_id = fields.Many2one(
        'res.partner',
        string='Nombre del Colaborador',
        required=True,
        tracking=True
    )
    
    # Campo 1.2: Número de cédula
    identification_number = fields.Char(
        string='Número de Cédula',
        required=True,
        tracking=True
    )
    
    # Campo 1.3: Organización
    company_id = fields.Many2one(
        'res.company',
        string='Organización',
        required=True,
        default=lambda self: self.env.company,
        tracking=True
    )
    
    # Campo 1.4: Tipo
    type = fields.Selection([
        ('direct', 'Directo'),
        ('service', 'Prestación de Servicios')
    ], string='Tipo', required=True, tracking=True)
    
    # Campo 1.5: Equipo
    department_id = fields.Many2one(
        'hr.department',
        string='Equipo',
        required=True,
        tracking=True
    )
    
    # Campo 1.6: Tipo de anticipo
    advance_type = fields.Selection([
        ('travel', 'Viaje'),
        ('purchase', 'Compra')
    ], string='Tipo de Anticipo', required=True, tracking=True)
    
    # Campo 1.7: Internacional
    is_international = fields.Selection([
        ('yes', 'SI'),
        ('no', 'NO')
    ], string='Internacional', required=True, tracking=True)
    
    # Campo 1.8: Ciudad de origen
    origin_city = fields.Char(string='Ciudad de Origen', tracking=True)
    
    # Campo 1.9: Ciudad destino
    destination_city = fields.Char(string='Ciudad Destino', tracking=True)
    
    # Campo 1.10: Fecha de salida
    departure_date = fields.Date(string='Fecha de Salida', tracking=True)
    
    # Campo 1.11: Fecha regreso
    return_date = fields.Date(string='Fecha de Regreso', tracking=True)
    
    # Campo 1.12: Compañía que debe legalizar el gasto
    expense_company_id = fields.Many2one(
        'res.company',
        string='Compañía que debe legalizar el gasto',
        required=True,
        tracking=True
    )
    
    # Campo 1.13: Monto
    amount = fields.Float(
        string='Monto',
        required=True,
        tracking=True
    )
    
    # Campo 1.14: Girar a nombre de
    pay_to_name = fields.Char(
        string='Girar a nombre de',
        required=True,
        tracking=True
    )
    
    # Campo 1.15: Número de cédula (del beneficiario)
    beneficiary_identification = fields.Char(
        string='Número de Cédula (Beneficiario)',
        required=True,
        tracking=True
    )
    
    # Campo 1.16: Adjuntar soporte
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Adjuntar soporte factura proforma / cuenta de cobro',
        tracking=True
    )
    
    # Campo 1.17: Fecha de entrega de anticipo
    delivery_date = fields.Date(
        string='Fecha de entrega de anticipo',
        tracking=True
    )
    
    # Campo 1.18: Fecha de presunta legalización
    legalization_date = fields.Date(
        string='Fecha de presunta legalización anticipo',
        compute='_compute_legalization_date',
        store=True,
        tracking=True
    )
    
    # Campo 1.19: Entregar a
    deliver_to = fields.Char(
        string='Entregar a',
        tracking=True
    )
    
    # Campo 1.20: Observaciones
    observations = fields.Text(
        string='Observaciones',
        tracking=True
    )
    
    # Campo 1.21: Aprobador
    approver_id = fields.Many2one(
        'res.users',
        string='Aprobador',
        required=True,
        domain=lambda self: [('groups_id', 'in', [self.env.ref('analytic_account_request.group_advance_request_approver').id])],
        tracking=True
    )
    
    # Campo 1.22: Proveedor/Empleado
    supplier_employee_id = fields.Many2one(
        'res.partner',
        string='Proveedor/Empleado',
        tracking=True,
        help='Tercero que se usará en la contabilización'
    )
    
    # Campos de control
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('requested', 'Solicitado'),
        ('approved', 'Aprobado'),
        ('accounted', 'Causado'),
        ('paid', 'Pagado'),
        ('done', 'Terminado'),
        ('cancelled', 'Cancelado')
    ], string='Estado', default='draft', tracking=True, required=True)
    
    cancel_reason = fields.Text(
        string='Razón de Cancelación',
        tracking=True
    )
    
    # Campos de aprobación financiera
    financial_approver_id = fields.Many2one(
        'res.users',
        string='Aprobador Financiero',
        tracking=True
    )
    
    financial_approved = fields.Boolean(
        string='Visto Bueno Financiero',
        default=False,
        tracking=True
    )
    
    financial_approval_date = fields.Datetime(
        string='Fecha Visto Bueno Financiero',
        readonly=True,
        tracking=True
    )
    
    # Relación con asiento contable
    move_id = fields.Many2one(
        'account.move',
        string='Asiento Contable',
        readonly=True,
        tracking=True
    )
    
    # Campos de auditoría
    request_date = fields.Datetime(
        string='Fecha de Solicitud',
        default=fields.Datetime.now,
        readonly=True,
        tracking=True
    )
    
    approval_date = fields.Datetime(
        string='Fecha de Aprobación',
        readonly=True,
        tracking=True
    )
    
    email = fields.Char(
        string='Email del Solicitante',
        related='partner_id.email',
        readonly=True
    )
    
    @api.depends('delivery_date')
    def _compute_legalization_date(self):
        """Calcula la fecha de legalización: 3 días después de la entrega"""
        for record in self:
            if record.delivery_date:
                delivery = fields.Date.from_string(record.delivery_date)
                record.legalization_date = delivery + timedelta(days=3)
            else:
                record.legalization_date = False
    
    @api.model
    def create(self, vals):
        """Generar secuencia al crear"""
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('advance.request') or 'Nuevo'
        return super(AdvanceRequest, self).create(vals)
    
    def action_submit(self):
        """Enviar solicitud - Cambiar a estado Solicitado"""
        for record in self:
            if record.state != 'draft':
                raise UserError('Solo se pueden enviar solicitudes en estado Borrador.')
            
            record.write({
                'state': 'requested',
                'request_date': fields.Datetime.now()
            })
            
            # Enviar correo al solicitante
            record.send_request_notification()
            
            # Enviar correo a aprobadores
            record.send_approver_notification()
        
        return True
    
    def action_approve(self):
        """Aprobar solicitud"""
        for record in self:
            if record.state != 'requested':
                raise UserError('Solo se pueden aprobar solicitudes en estado Solicitado.')
            
            # Validar que el usuario actual sea el aprobador
            if record.approver_id.id != self.env.user.id:
                raise UserError('Solo el aprobador designado puede aprobar esta solicitud.')
            
            record.write({
                'state': 'approved',
                'approval_date': fields.Datetime.now()
            })
        
        return True
    
    def action_financial_approval(self):
        """Dar visto bueno financiero"""
        for record in self:
            if record.state != 'approved':
                raise UserError('Solo se puede dar visto bueno financiero en estado Aprobado.')
            
            # Obtener el aprobador financiero configurado
            financial_approver_param = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.default_financial_advance_approver_id'
            )
            
            if not financial_approver_param:
                raise UserError('No se ha configurado el aprobador financiero por defecto. Por favor configure en Ajustes.')
            
            financial_approver_id = int(financial_approver_param)
            
            # Validar que el usuario actual sea el aprobador financiero
            if self.env.user.id != financial_approver_id:
                raise UserError('Solo el aprobador financiero designado puede dar el visto bueno.')
            
            record.write({
                'financial_approved': True,
                'financial_approval_date': fields.Datetime.now(),
                'financial_approver_id': self.env.user.id
            })
        
        return True
    
    def action_account(self):
        """Causar - Crear asiento contable"""
        for record in self:
            if record.state != 'approved':
                raise UserError('Solo se pueden causar solicitudes en estado Aprobado.')
            
            if not record.financial_approved:
                raise UserError('Debe tener el visto bueno financiero antes de causar.')
            
            if not record.supplier_employee_id:
                raise UserError('Debe llenar el campo Proveedor/Empleado antes de causar.')
            
            # Obtener parámetros de configuración
            journal_param = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.advance_journal_id'
            )
            cxp_account_param = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.advance_cxp_account_id'
            )
            cxc_account_param = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.advance_cxc_account_id'
            )
            cxc_employee_account_param = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.advance_cxc_employee_account_id'
            )
            
            if not journal_param or not cxp_account_param or not cxc_account_param:
                raise UserError('Faltan parámetros de contabilización. Por favor configure en Ajustes:\n'
                              '- Diario de Anticipos\n'
                              '- Cuenta CXP\n'
                              '- Cuenta CXC')
            
            journal_id = int(journal_param)
            cxp_account_id = int(cxp_account_param)
            
            # Verificar si el proveedor/empleado es un empleado
            is_employee = self.env['hr.employee'].sudo().search([
                ('work_contact_id', '=', record.supplier_employee_id.id)
            ], limit=1)
            
            # Seleccionar la cuenta CXC apropiada
            if is_employee and cxc_employee_account_param:
                cxc_account_id = int(cxc_employee_account_param)
                account_type = "empleado"
            else:
                cxc_account_id = int(cxc_account_param)
                account_type = "tercero"
            
            # Crear asiento contable
            move_vals = {
                'journal_id': journal_id,
                'date': fields.Date.today(),
                'ref': f'CONTABILIZACION ANTICIPOS {record.name} ({account_type})',
                'line_ids': [
                    # Línea CXP al crédito
                    (0, 0, {
                        'account_id': cxp_account_id,
                        'partner_id': record.supplier_employee_id.id,
                        'name': record.observations or 'Anticipo',
                        'credit': record.amount,
                        'debit': 0.0,
                    }),
                    # Línea CXC al débito
                    (0, 0, {
                        'account_id': cxc_account_id,
                        'partner_id': record.supplier_employee_id.id,
                        'name': record.observations or 'Anticipo',
                        'debit': record.amount,
                        'credit': 0.0,
                    }),
                ]
            }
            
            move = self.env['account.move'].create(move_vals)
            
            record.write({
                'move_id': move.id,
                'state': 'accounted'
            })
        
        return True
    
    def action_mark_as_paid(self):
        """Marcar como pagado"""
        for record in self:
            if record.state != 'accounted':
                raise UserError('Solo se pueden marcar como pagadas solicitudes en estado Causado.')
            
            record.write({
                'state': 'paid'
            })
            
            # Enviar correo al solicitante
            record.send_payment_notification()
        
        return True
    
    def action_done(self):
        """Terminar solicitud"""
        for record in self:
            if record.state != 'paid':
                raise UserError('Solo se pueden terminar solicitudes en estado Pagado.')
            
            record.write({
                'state': 'done'
            })
            
            # Enviar correo al solicitante
            record.send_done_notification()
        
        return True
    
    def action_cancel(self):
        """Abrir wizard de cancelación"""
        return {
            'name': 'Cancelar Solicitud',
            'type': 'ir.actions.act_window',
            'res_model': 'advance.request.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_request_id': self.id
            }
        }
    
    def action_view_move(self):
        """Ver asiento contable"""
        self.ensure_one()
        if not self.move_id:
            raise UserError('No hay asiento contable asociado a esta solicitud.')
        
        return {
            'name': 'Asiento Contable',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
        }
    
    def send_request_notification(self):
        """Enviar correo de confirmación al solicitante"""
        import logging
        _logger = logging.getLogger(__name__)
        
        template = self.env.ref('analytic_account_request.email_template_advance_request_confirmation', raise_if_not_found=False)
        if template:
            for record in self:
                _logger.info(f"Sending request confirmation email to {record.partner_id.email} for request {record.name}")
                try:
                    # Enviar email y registrar en el chatter
                    template.send_mail(record.id, force_send=True, notif_layout='mail.mail_notification_light')
                    # Agregar mensaje al chatter
                    record.message_post(
                        body=f"Correo de confirmación enviado a {record.partner_id.name} ({record.partner_id.email})",
                        subject="Solicitud Enviada",
                        message_type='notification',
                    )
                    _logger.info(f"Email sent successfully to {record.partner_id.email}")
                except Exception as e:
                    _logger.error(f"Error sending email: {str(e)}")
        else:
            _logger.warning("Email template 'email_template_advance_request_confirmation' not found")
    
    def send_approver_notification(self):
        """Enviar correo a aprobadores"""
        import logging
        _logger = logging.getLogger(__name__)
        
        template = self.env.ref('analytic_account_request.email_template_advance_request_approval', raise_if_not_found=False)
        if template:
            for record in self:
                _logger.info(f"Sending approval notification email to {record.approver_id.email} for request {record.name}")
                try:
                    # Enviar email y registrar en el chatter
                    template.send_mail(record.id, force_send=True, notif_layout='mail.mail_notification_light')
                    # Agregar mensaje al chatter
                    record.message_post(
                        body=f"Notificación de aprobación enviada a {record.approver_id.name} ({record.approver_id.email})",
                        subject="Enviado a Aprobador",
                        message_type='notification',
                    )
                    _logger.info(f"Email sent successfully to {record.approver_id.email}")
                except Exception as e:
                    _logger.error(f"Error sending email: {str(e)}")
        else:
            _logger.warning("Email template 'email_template_advance_request_approval' not found")
    
    def send_payment_notification(self):
        """Enviar correo de pago al solicitante"""
        import logging
        _logger = logging.getLogger(__name__)
        
        template = self.env.ref('analytic_account_request.email_template_advance_request_payment', raise_if_not_found=False)
        if template:
            for record in self:
                _logger.info(f"Sending payment notification email to {record.partner_id.email} for request {record.name}")
                try:
                    # Enviar email y registrar en el chatter
                    template.send_mail(record.id, force_send=True, notif_layout='mail.mail_notification_light')
                    # Agregar mensaje al chatter
                    record.message_post(
                        body=f"Notificación de pago enviada a {record.partner_id.name} ({record.partner_id.email})",
                        subject="Anticipo Pagado",
                        message_type='notification',
                    )
                    _logger.info(f"Email sent successfully to {record.partner_id.email}")
                except Exception as e:
                    _logger.error(f"Error sending email: {str(e)}")
        else:
            _logger.warning("Email template 'email_template_advance_request_payment' not found")
    
    def send_done_notification(self):
        """Enviar correo de finalización al solicitante"""
        import logging
        _logger = logging.getLogger(__name__)
        
        template = self.env.ref('analytic_account_request.email_template_advance_request_done', raise_if_not_found=False)
        if template:
            for record in self:
                _logger.info(f"Sending done notification email to {record.partner_id.email} for request {record.name}")
                try:
                    # Enviar email y registrar en el chatter
                    template.send_mail(record.id, force_send=True, notif_layout='mail.mail_notification_light')
                    # Agregar mensaje al chatter
                    record.message_post(
                        body=f"Notificación de finalización enviada a {record.partner_id.name} ({record.partner_id.email})",
                        subject="Solicitud Finalizada",
                        message_type='notification',
                    )
                    _logger.info(f"Email sent successfully to {record.partner_id.email}")
                except Exception as e:
                    _logger.error(f"Error sending email: {str(e)}")
        else:
            _logger.warning("Email template 'email_template_advance_request_done' not found")


class AdvanceRequestCancelWizard(models.TransientModel):
    _name = 'advance.request.cancel.wizard'
    _description = 'Wizard de Cancelación de Solicitud de Anticipo'

    request_id = fields.Many2one('advance.request', string='Solicitud', required=True)
    cancel_reason = fields.Text(string='Razón de Cancelación', required=True)

    def action_confirm_cancel(self):
        """Confirmar cancelación"""
        self.ensure_one()
        self.request_id.write({
            'state': 'cancelled',
            'cancel_reason': self.cancel_reason
        })
        return {'type': 'ir.actions.act_window_close'}
