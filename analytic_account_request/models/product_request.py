# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProductRequest(models.Model):
    _name = 'product.request'
    _description = 'Solicitud de Creación de Producto'
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
    
    # Información del producto
    company_id = fields.Many2one(
        'res.company',
        string='Organización',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        help='Organización para la cual se va crear el Producto'
    )
    
    product_type = fields.Selection([
        ('existing', 'Existente (Producto ya Creado en Odoo)'),
        ('new', 'Nuevo (Que no está en el portafolio actualmente)'),
        ('variants', 'Variantes (Forma de venta/Paquete-Referencia-Tiempo-Alcance del servicio-Promociones)'),
    ], string='Producto en Odoo', required=True, tracking=True)
    
    product_name = fields.Char(
        string='Nombre del Producto',
        required=True,
        tracking=True
    )
    
    product_justification = fields.Text(
        string='Justificación del Producto',
        required=True,
        tracking=True
    )
    
    disclosure_medium = fields.Selection([
        ('virtual_store', 'Tienda Virtual'),
        ('direct_negotiation', 'Negociación Directa'),
    ], string='Medio de Divulgación del Producto', required=True, tracking=True)
    
    has_variants = fields.Selection([
        ('yes', 'Sí'),
        ('no', 'No'),
    ], string='Variantes', required=True, tracking=True)
    
    variants_file = fields.Binary(
        string='Archivo de Variantes',
        help='Adjuntar archivo identificando y explicando cada variante',
        tracking=True
    )
    
    variants_filename = fields.Char(
        string='Nombre del Archivo de Variantes'
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica del Producto',
        required=True,
        domain="[('company_id', '=', company_id)]",
        tracking=True
    )
    
    is_deferred = fields.Boolean(
        string='Producto es Diferido',
        default=False,
        tracking=True
    )
    
    deferred_time = fields.Integer(
        string='A Cuánto Tiempo se Difiere',
        help='Tiempo en meses',
        tracking=True
    )
    
    payment_method = fields.Selection([
        ('advance', 'Anticipado'),
        ('credit', 'A crédito'),
    ], string='Forma de Pago', required=True, tracking=True)
    
    policy_responsible = fields.Char(
        string='Responsable de las Políticas del Producto',
        required=True,
        tracking=True
    )
    
    # ASPECTOS LEGALES
    legal_purpose = fields.Text(
        string='Objeto',
        help='El propósito del contrato descrito de forma precisa. Permite definir la naturaleza jurídica de la relación que surge entre las partes',
        tracking=True
    )
    
    specific_objectives = fields.Text(
        string='Objetivos Específicos',
        help='Si los hubiere es una relación detallada de los diversos propósitos que se pretenden con el contrato. Se pueden asociar a los denominados productos',
        tracking=True
    )
    
    scope = fields.Text(
        string='Alcance',
        tracking=True
    )
    
    duration = fields.Text(
        string='Duración',
        help='Tiempo que las partes determinan para su ejecución e indicación de la posibilidad de prórroga, si las partes la pactan',
        tracking=True
    )
    
    place = fields.Text(
        string='Lugar',
        help='Lugar o lugares donde se ejecutará el contrato o se prestarán los servicios, cuando sea procedente',
        tracking=True
    )
    
    price = fields.Text(
        string='Precio',
        help='Determinación del monto del contrato o la forma de su determinación si no fuera determinado sino determinable, expresado en moneda colombiana o extranjera y tasa para la conversión en pesos, si fuere el caso',
        tracking=True
    )
    
    logyca_obligations = fields.Text(
        string='Obligaciones LOGYCA',
        help='Relación de todas las obligaciones que surgen para LOGYCA de la celebración del contrato o convenio. La descripción debe ser precisa y la relación exhaustiva. (De dar, hacer o no hacer)',
        tracking=True
    )
    
    acceptor_obligations = fields.Text(
        string='Obligaciones del Aceptante',
        help='Especificar a qué se compromete el aceptante',
        tracking=True
    )
    
    termination_causes = fields.Text(
        string='Causales Especiales de Terminación',
        help='Condiciones o circunstancias especiales que dieren lugar a la terminación del contrato o convenio de forma anticipada, diversas del mutuo acuerdo y el incumplimiento de las obligaciones',
        tracking=True
    )
    
    liquidation_method = fields.Text(
        string='Forma de Liquidación',
        help='En el evento de una terminación anticipada del contrato o convenio y se encuentren obligaciones en ejecución, describa la forma como se deberá prever su prestación y la forma de reconocimiento o pago de los derechos a que hubiere lugar',
        tracking=True
    )
    
    contract_assignment = fields.Text(
        string='Cesión del Contrato',
        help='Indicar si hay posibilidad de cesión del contrato y si se requiere autorización previa o no',
        tracking=True
    )
    
    penalty_clause = fields.Text(
        string='Condiciones de Cláusula Penal',
        help='Por favor especificar las condiciones, en caso de requerir cláusula penal',
        tracking=True
    )
    
    observations = fields.Text(
        string='Observaciones',
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
    
    # Aprobaciones múltiples
    financial_approver_id = fields.Many2one(
        'res.users',
        string='Autoriza Estructura Financiera',
        tracking=True,
        help='Usuario que autoriza desde el punto de vista financiero'
    )
    
    financial_approved = fields.Boolean(
        string='Aprobado Estructura Financiera',
        default=False,
        tracking=True
    )
    
    financial_approval_date = fields.Datetime(
        string='Fecha Aprobación Financiera',
        readonly=True,
        tracking=True
    )
    
    legal_approver_id = fields.Many2one(
        'res.users',
        string='Autoriza Temas Legales',
        tracking=True,
        help='Usuario que autoriza desde el punto de vista legal'
    )
    
    legal_approved = fields.Boolean(
        string='Aprobado Temas Legales',
        default=False,
        tracking=True
    )
    
    legal_approval_date = fields.Datetime(
        string='Fecha Aprobación Legal',
        readonly=True,
        tracking=True
    )
    
    accounting_approver_id = fields.Many2one(
        'res.users',
        string='Autoriza Estructura Contable',
        tracking=True,
        help='Usuario que autoriza desde el punto de vista contable'
    )
    
    accounting_approved = fields.Boolean(
        string='Aprobado Estructura Contable',
        default=False,
        tracking=True
    )
    
    accounting_approval_date = fields.Datetime(
        string='Fecha Aprobación Contable',
        readonly=True,
        tracking=True
    )
    
    all_approved = fields.Boolean(
        string='Todas las Aprobaciones Completas',
        compute='_compute_all_approved',
        store=True
    )
    
    # Campo activo
    active = fields.Boolean(
        string='Activo',
        default=True
    )

    product_id = fields.Many2one(
        'product.template',
        string='Producto',
        readonly=True,
        tracking=True
    )


    @api.depends('financial_approved', 'legal_approved', 'accounting_approved')
    def _compute_all_approved(self):
        """
        Verifica si todas las aprobaciones están completas
        """
        for record in self:
            record.all_approved = (
                record.financial_approved and 
                record.legal_approved and 
                record.accounting_approved
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
    
    @api.onchange('is_deferred')
    def _onchange_is_deferred(self):
        """
        Limpia el campo deferred_time cuando is_deferred es False
        """
        if not self.is_deferred:
            self.deferred_time = 0
    
    @api.model
    def create(self, vals):
        """
        Override create para generar la secuencia del nombre y establecer aprobadores por defecto
        """
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('product.request') or 'Nuevo'
        
        # Establecer aprobadores por defecto desde parámetros del sistema
        if not vals.get('financial_approver_id'):
            financial_approver = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.default_financial_approver_id'
            )
            if financial_approver:
                vals['financial_approver_id'] = int(financial_approver)
        
        if not vals.get('legal_approver_id'):
            legal_approver = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.default_legal_approver_id'
            )
            if legal_approver:
                vals['legal_approver_id'] = int(legal_approver)
        
        if not vals.get('accounting_approver_id'):
            accounting_approver = self.env['ir.config_parameter'].sudo().get_param(
                'analytic_account_request.default_accounting_approver_id'
            )
            if accounting_approver:
                vals['accounting_approver_id'] = int(accounting_approver)
        
        return super(ProductRequest, self).create(vals)
    
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
        Aprueba la solicitud - Solo cuando todas las aprobaciones estén completas
        """
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_('Solo se pueden aprobar solicitudes en estado Solicitado.'))
        
        # Verificar que todas las aprobaciones estén completas
        if not self.all_approved:
            pending = []
            if not self.financial_approved:
                pending.append('Estructura Financiera')
            if not self.legal_approved:
                pending.append('Temas Legales')
            if not self.accounting_approved:
                pending.append('Estructura Contable')
            
            raise UserError(_('No se puede aprobar la solicitud. Faltan las siguientes aprobaciones:\n- %s') % '\n- '.join(pending))
        
        self.write({'state': 'approved'})
        
        return True
    
    def action_approve_financial(self):
        """
        Aprobación de Estructura Financiera
        """
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_('Solo se pueden aprobar solicitudes en estado Solicitado.'))
        
        # Verificar que el usuario actual es el aprobador financiero
        if self.financial_approver_id and self.financial_approver_id.id != self.env.user.id:
            raise UserError(_('Solo el usuario %s puede aprobar desde Estructura Financiera.') % self.financial_approver_id.name)
        
        self.write({
            'financial_approved': True,
            'financial_approval_date': fields.Datetime.now(),
        })
        
        # Si todas las aprobaciones están completas, cambiar a aprobado automáticamente
        if self.all_approved:
            self.write({'state': 'approved'})
        
        return True
    
    def action_approve_legal(self):
        """
        Aprobación de Temas Legales
        """
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_('Solo se pueden aprobar solicitudes en estado Solicitado.'))
        
        # Verificar que el usuario actual es el aprobador legal
        if self.legal_approver_id and self.legal_approver_id.id != self.env.user.id:
            raise UserError(_('Solo el usuario %s puede aprobar desde Temas Legales.') % self.legal_approver_id.name)
        
        self.write({
            'legal_approved': True,
            'legal_approval_date': fields.Datetime.now(),
        })
        
        # Si todas las aprobaciones están completas, cambiar a aprobado automáticamente
        if self.all_approved:
            self.write({'state': 'approved'})
        
        return True
    
    def action_approve_accounting(self):
        """
        Aprobación de Estructura Contable
        """
        self.ensure_one()
        
        if self.state != 'requested':
            raise UserError(_('Solo se pueden aprobar solicitudes en estado Solicitado.'))
        
        # Verificar que el usuario actual es el aprobador contable
        if self.accounting_approver_id and self.accounting_approver_id.id != self.env.user.id:
            raise UserError(_('Solo el usuario %s puede aprobar desde Estructura Contable.') % self.accounting_approver_id.name)
        
        self.write({
            'accounting_approved': True,
            'accounting_approval_date': fields.Datetime.now(),
        })
        
        # Si todas las aprobaciones están completas, cambiar a aprobado automáticamente
        if self.all_approved:
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
            'res_model': 'product.request.cancel.wizard',
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
        approver_group = self.env.ref('analytic_account_request.group_product_request_approver', raise_if_not_found=False)
        
        if approver_group and approver_group.users:
            # Obtener emails de los usuarios del grupo
            approver_emails = [user.email for user in approver_group.users if user.email]
            
            if approver_emails:
                template = self.env.ref('analytic_account_request.email_template_product_approval', raise_if_not_found=False)
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
                            'name': 'Product Request Notification',
                            'type': 'server',
                            'level': 'info',
                            'message': f'Notificación enviada a aprobadores: {email_to}',
                            'path': 'product.request',
                            'func': 'send_approval_notification',
                            'line': '0',
                        })
                        
                        return True
                    except Exception as e:
                        # Log del error
                        self.env['ir.logging'].sudo().create({
                            'name': 'Product Approval Notification Error',
                            'type': 'server',
                            'level': 'error',
                            'message': f'Error enviando notificación: {str(e)}',
                            'path': 'product.request',
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
            template = self.env.ref('analytic_account_request.email_template_product_submission', raise_if_not_found=False)
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
                        'name': 'Product Submission Confirmation Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando confirmación: {str(e)}',
                        'path': 'product.request',
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
            template = self.env.ref('analytic_account_request.email_template_product_completion', raise_if_not_found=False)
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
                        'name': 'Product Completion Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de completación: {str(e)}',
                        'path': 'product.request',
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
            template = self.env.ref('analytic_account_request.email_template_product_cancellation', raise_if_not_found=False)
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
                        'name': 'Product Cancellation Notification Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando notificación de cancelación: {str(e)}',
                        'path': 'product.request',
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
        return f"{base_url}/web#id={self.id}&view_type=form&model=product.request"

    def action_done(self):
        """
        Crea la cuenta analítica basada en la solicitud
        """
        self.ensure_one()
        
        if self.state != 'approved':
            raise UserError(_('Solo se pueden crear cuentas analíticas de solicitudes aprobadas.'))
        
        if self.product_id:
            raise UserError(_('Esta solicitud ya tiene un producto creada.'))
        
        # Crear la cuenta analítica
        product_account = self.env['product.template'].create({
            'name': self.product_name,
            'x_is_deferred': self.is_deferred,
            'sale_ok': True,
            'company_id': self.company_id.id,
        })
        
        self.write({
            'product_id': product_account.id,
            'state': 'done'
        })
        
        # Enviar notificación al solicitante
        self.send_completion_notification()
        
        return {
            'name': _('Producto Creado'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': product_account.id,
            'view_mode': 'form',
            'target': 'current',
        }        

class ProductRequestCancelWizard(models.TransientModel):
    _name = 'product.request.cancel.wizard'
    _description = 'Wizard para Cancelar Solicitud de Producto'
    
    request_id = fields.Many2one(
        'product.request',
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
