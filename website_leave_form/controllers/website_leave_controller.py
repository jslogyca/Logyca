# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from datetime import datetime
import base64

class WebsiteLeaveController(http.Controller):

    @http.route('/ausencias/formulario', type='http', auth='public', website=True, csrf=False)
    def leave_form(self, **kwargs):
        """Muestra el formulario de ausencias"""
        leave_types = request.env['hr.leave.type'].sudo().search([])
        # Obtener empleados que pueden ser aprobadores (puedes filtrar por departamento, manager, etc.)
        approvers = request.env['hr.employee'].sudo().search([
            '|', ('parent_id', '!=', False), ('job_id.name', 'ilike', 'manager')
        ])
        
        # Fecha actual para el campo fecha de solicitud
        today = fields.Date.context_today(request.env['hr.leave'])
        
        values = {
            'leave_types': leave_types,
            'approvers': approvers,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
        }
        return request.render('website_leave_form.leave_form_template', values)

    @http.route('/ausencias/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_leave(self, **post):
        """Procesa el envío del formulario"""
        try:
            # Validar datos requeridos
            required_fields = ['name', 'email', 'holiday_status_id', 'approver_id', 'date_from', 'date_to']
            for field in required_fields:
                if not post.get(field):
                    return request.redirect('/ausencias/formulario?error=Todos los campos obligatorios deben ser completados')

            # Buscar empleado por email
            employee = request.env['hr.employee'].sudo().search([
                ('work_email', '=', post.get('email'))
            ], limit=1)

            if not employee:
                return request.redirect('/ausencias/formulario?error=No se encontró un empleado con ese email')

            # Verificar si el tipo de ausencia requiere adjuntos
            leave_type = request.env['hr.leave.type'].sudo().browse(int(post.get('holiday_status_id')))
            attachments = request.httprequest.files.getlist('attachments')
            
            if leave_type.require_attachment and not attachments:
                return request.redirect('/ausencias/formulario?error=Este tipo de ausencia requiere adjuntar documentos de soporte')

            # Convertir fechas
            date_from = datetime.strptime(post.get('date_from'), '%Y-%m-%dT%H:%M')
            date_to = datetime.strptime(post.get('date_to'), '%Y-%m-%dT%H:%M')
            request_date = datetime.strptime(post.get('request_date'), '%Y-%m-%d').date() if post.get('request_date') else fields.Date.context_today(request.env['hr.leave'])

            # Procesar archivos adjuntos
            attachment_ids = []
            for file in attachments:
                if file and file.filename:
                    file_content = file.read()
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': file.filename,
                        'datas': base64.b64encode(file_content),
                        'res_model': 'website.leave.form',
                        'res_id': 0,  # Se actualizará después
                        'public': False,
                    })
                    attachment_ids.append(attachment.id)

            # Crear la ausencia con aprobador
            leave_vals = {
                'employee_id': employee.id,
                'holiday_status_id': int(post.get('holiday_status_id')),
                'request_date_from': date_from.date(),
                'request_date_to': date_to.date(),
                'date_from': date_from,
                'date_to': date_to,
                'name': post.get('notes', 'Solicitud desde formulario web'),
            }

            leave = request.env['hr.leave'].sudo().create(leave_vals)
            
            # Adjuntar archivos a la ausencia
            if attachment_ids:
                for att_id in attachment_ids:
                    request.env['ir.attachment'].sudo().browse(att_id).write({
                        'res_model': 'hr.leave',
                        'res_id': leave.id,
                    })
            
            # Asignar el aprobador a la ausencia
            approver_id = int(post.get('approver_id'))
            approver = request.env['hr.employee'].sudo().browse(approver_id)
            
            if approver and approver.user_id:
                leave.sudo().write({'approver_id': approver.user_id.id})

            # Guardar registro en el modelo temporal
            leave_form = request.env['website.leave.form'].sudo().create({
                'name': post.get('name'),
                'email': post.get('email'),
                'employee_id': employee.id,
                'holiday_status_id': int(post.get('holiday_status_id')),
                'approver_id': approver_id,
                'date_from': date_from,
                'date_to': date_to,
                'request_date': request_date,
                'notes': post.get('notes', ''),
                'state': 'submitted',
                'leave_id': leave.id,
                'attachment_ids': [(6, 0, attachment_ids)] if attachment_ids else False,
            })

            # Actualizar res_id de los adjuntos en website.leave.form
            if attachment_ids:
                for att_id in attachment_ids:
                    request.env['ir.attachment'].sudo().browse(att_id).write({
                        'res_model': 'website.leave.form',
                        'res_id': leave_form.id,
                    })

            # Enviar email al aprobador
            if approver and approver.work_email:
                template = request.env.ref('website_leave_form.email_template_leave_approval', raise_if_not_found=False)
                if template:
                    template.sudo().send_mail(leave_form.id, force_send=True, email_values={
                        'email_to': approver.work_email,
                    })

            return request.redirect('/ausencias/formulario?success=Solicitud de ausencia creada exitosamente. El aprobador ha sido notificado por correo electrónico.')

        except Exception as e:
            return request.redirect(f'/ausencias/formulario?error=Error al procesar la solicitud: {str(e)}')

    @http.route('/ausencias/consultar', type='http', auth='public', website=True, csrf=False)
    def leave_query_form(self, **kwargs):
        """Muestra el formulario de consulta de ausencias"""
        values = {
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
        }
        return request.render('website_leave_form.leave_query_template', values)

    @http.route('/ausencias/consultar/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_leave_query(self, **post):
        """Procesa la consulta de ausencias y envía el resumen por email"""
        try:
            # Validar datos requeridos
            identification_id = post.get('identification_id', '').strip()
            date_from = post.get('date_from')
            date_to = post.get('date_to')

            if not identification_id or not date_from or not date_to:
                return request.redirect('/ausencias/consultar?error=Todos los campos son obligatorios')

            # Buscar empleado por número de identificación
            employee = request.env['hr.employee'].sudo().search([
                ('identification_id', '=', identification_id)
            ], limit=1)

            if not employee:
                return request.redirect('/ausencias/consultar?error=No se encontró un empleado con ese número de identificación')

            if not employee.work_email:
                return request.redirect('/ausencias/consultar?error=El empleado no tiene un email corporativo registrado')

            # Convertir fechas
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')

            # Buscar ausencias aprobadas en el rango de fechas
            leaves = request.env['hr.leave'].sudo().search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', date_from_dt.date()),
                ('request_date_to', '<=', date_to_dt.date()),
            ], order='request_date_from desc')

            if not leaves:
                return request.redirect('/ausencias/consultar?error=No se encontraron ausencias aprobadas en el rango de fechas especificado')

            # Enviar email con el resumen
            template = request.env.ref('website_leave_form.email_template_leave_summary', raise_if_not_found=False)
            if template:
                # Preparar contexto para el template
                ctx = {
                    'employee': employee,
                    'leaves': leaves,
                    'date_from': date_from_dt.strftime('%d/%m/%Y'),
                    'date_to': date_to_dt.strftime('%d/%m/%Y'),
                }
                
                # Enviar el email
                template.sudo().with_context(ctx).send_mail(
                    employee.id,
                    force_send=True,
                    email_values={
                        'email_to': employee.work_email,
                    }
                )

            return request.redirect(f'/ausencias/consultar?success=Se ha enviado el resumen de ausencias al correo {employee.work_email}')

        except Exception as e:
            return request.redirect(f'/ausencias/consultar?error=Error al procesar la consulta: {str(e)}')