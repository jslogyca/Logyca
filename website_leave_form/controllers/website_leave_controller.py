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
        
        # Obtener el email del parámetro si existe (para pre-cargar aprobadores)
        email = kwargs.get('email', '')
        approvers = request.env['res.partner'].sudo()
        
        if email:
            # Buscar empleado por email para cargar sus aprobadores disponibles
            # NOTA: Búsqueda sin restricción de compañía para soportar multi-compañía
            employee = request.env['hr.employee'].sudo().search([
                ('work_email', '=', email)
            ], limit=1)
            
            if employee and employee.parent_id:
                # Obtener el partner relacionado al parent_id del empleado
                parent_partner = employee.parent_id
                
                # Solo usar work_contact_id como aprobador (no sus contactos relacionados)
                if parent_partner.work_contact_id:
                    main_contact = parent_partner.work_contact_id
                    approvers = request.env['res.partner'].sudo().search([
                        ('id', '=', main_contact.id)
                    ])
                # Si no tiene work_contact_id, no hay aprobadores (approvers queda vacío)
        
        # Fecha actual para el campo fecha de solicitud
        today = fields.Date.context_today(request.env['hr.leave'])
        
        values = {
            'leave_types': leave_types,
            'approvers': approvers,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
            'email': email,
        }
        return request.render('website_leave_form.leave_form_template', values)

    @http.route('/ausencias/get_approvers', type='json', auth='public', website=True, csrf=False)
    def get_approvers(self, email):
        """Obtiene los aprobadores disponibles para un email dado"""
        approvers_data = []
        
        if email:
            # Buscar empleado por email
            # NOTA: Búsqueda sin restricción de compañía para soportar multi-compañía
            employee = request.env['hr.employee'].sudo().search([
                ('work_email', '=', email)
            ], limit=1)
            
            if employee and employee.parent_id:
                # Obtener el partner relacionado al parent_id del empleado
                parent_partner = employee.parent_id
                
                # Solo usar work_contact_id como aprobador (no sus contactos relacionados)
                if parent_partner.work_contact_id:
                    main_contact = parent_partner.work_contact_id
                    approvers = request.env['res.partner'].sudo().search([
                        ('id', '=', main_contact.id)
                    ])
                    approvers_data = [{'id': a.id, 'name': a.name} for a in approvers]
                # Si no tiene work_contact_id, no hay aprobadores (approvers_data queda vacío)
        
        return approvers_data

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
            # NOTA: Búsqueda sin restricción de compañía para soportar multi-compañía
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

            # Validar que el aprobador existe
            approver_id = int(post.get('approver_id'))
            approver = request.env['res.partner'].sudo().browse(approver_id)
            
            if not approver.exists():
                return request.redirect('/ausencias/formulario?error=El aprobador seleccionado no es válido')

            # Procesar archivos adjuntos
            attachment_ids = []
            if attachments:
                for file in attachments:
                    if file and hasattr(file, 'filename') and file.filename:
                        file_content = file.read()
                        attachment = request.env['ir.attachment'].sudo().create({
                            'name': file.filename,
                            'datas': base64.b64encode(file_content),
                            'res_model': 'hr.leave',
                            'res_id': 0,  # Se actualizará después
                            'public': False,
                            'mimetype': file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
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
            
            # Adjuntar archivos a la ausencia creada
            if attachment_ids:
                request.env['ir.attachment'].sudo().browse(attachment_ids).write({
                    'res_model': 'hr.leave',
                    'res_id': leave.id,
                })
            
            # Crear actividad para el aprobador (buscar usuario relacionado al partner)
            if approver:
                try:
                    # Buscar el usuario relacionado al partner aprobador
                    approver_user = request.env['res.users'].sudo().search([
                        ('partner_id', '=', approver.id)
                    ], limit=1)
                    
                    if approver_user:
                        activity_type = request.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                        if activity_type:
                            request.env['mail.activity'].sudo().create({
                                'activity_type_id': activity_type.id,
                                'res_id': leave.id,
                                'res_model_id': request.env['ir.model'].sudo().search([('model', '=', 'hr.leave')], limit=1).id,
                                'user_id': approver_user.id,
                                'summary': 'Aprobar solicitud de ausencia',
                                'note': f'Nueva solicitud de ausencia de {employee.name} para aprobación.',
                            })
                except Exception as e:
                    # Si falla la creación de actividad, continuar (no es crítico)
                    pass

            # Guardar registro en el modelo temporal con una copia de los adjuntos
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
            })
            
            # Crear copias de los adjuntos para website.leave.form (para auditoría)
            if attachment_ids:
                for att_id in attachment_ids:
                    original_att = request.env['ir.attachment'].sudo().browse(att_id)
                    request.env['ir.attachment'].sudo().create({
                        'name': original_att.name,
                        'datas': original_att.datas,
                        'res_model': 'website.leave.form',
                        'res_id': leave_form.id,
                        'public': False,
                        'mimetype': original_att.mimetype,
                    })

            # Enviar email al aprobador
            if approver and approver.email:
                try:
                    template = request.env.ref('website_leave_form.email_template_leave_approval', raise_if_not_found=False)
                    if template:
                        # Enviar el email
                        mail_id = template.sudo().send_mail(
                            leave_form.id, 
                            force_send=True, 
                            email_values={
                                'email_to': approver.email,
                                'subject': f'Nueva Solicitud de Ausencia - {employee.name}',
                            }
                        )
                        
                        # Log de éxito
                        request.env['ir.logging'].sudo().create({
                            'name': 'Leave Approval Email Sent',
                            'type': 'server',
                            'level': 'info',
                            'message': f'Email de notificación enviado exitosamente a {approver.email} para la ausencia {leave.id}',
                            'path': 'website_leave_form',
                            'func': 'submit_leave',
                            'line': '0',
                        })
                    else:
                        # Log si no se encuentra el template
                        request.env['ir.logging'].sudo().create({
                            'name': 'Leave Approval Email Template Not Found',
                            'type': 'server',
                            'level': 'warning',
                            'message': 'No se encontró el template de email email_template_leave_approval',
                            'path': 'website_leave_form',
                            'func': 'submit_leave',
                            'line': '0',
                        })
                except Exception as e:
                    # Log de error pero no fallar la solicitud
                    request.env['ir.logging'].sudo().create({
                        'name': 'Leave Approval Email Error',
                        'type': 'server',
                        'level': 'error',
                        'message': f'Error enviando email a {approver.email}: {str(e)}',
                        'path': 'website_leave_form',
                        'func': 'submit_leave',
                        'line': '0',
                    })
            elif approver and not approver.email:
                # Log si el aprobador no tiene email
                request.env['ir.logging'].sudo().create({
                    'name': 'Leave Approval No Email',
                    'type': 'server',
                    'level': 'warning',
                    'message': f'El aprobador {approver.name} no tiene email configurado',
                    'path': 'website_leave_form',
                    'func': 'submit_leave',
                    'line': '0',
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
            # NOTA: Búsqueda sin restricción de compañía para soportar multi-compañía
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
