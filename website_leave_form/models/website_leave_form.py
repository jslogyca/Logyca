# -*- coding: utf-8 -*-
from odoo import http, fields, models, _
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
    approver_id = fields.Many2one('hr.employee', 'Aprobador', required=True)
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
