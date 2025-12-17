# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
from datetime import datetime

class AnalyticAccountRequestController(http.Controller):

    @http.route('/cuentas_analiticas/formulario', type='http', auth='public', website=True, csrf=False)
    def request_form(self, **kwargs):
        """Muestra el formulario de solicitud de cuentas analíticas"""
        
        # Obtener partners disponibles (asociados a empleados)
        employees = request.env['hr.employee'].sudo().search([('active', '=', True)])
        partners = employees.mapped('work_contact_id')
        
        # Obtener compañías
        companies = request.env['res.company'].sudo().search([])
        
        # Obtener planes analíticos
        plans = request.env['account.analytic.plan'].sudo().search([])
        
        # Fecha actual
        today = fields.Date.context_today(request.env['analytic.account.request'])
        
        values = {
            'partners': partners,
            'companies': companies,
            'plans': plans,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
            'request_number': kwargs.get('request_number', ''),
        }
        return request.render('analytic_account_request.request_form_template', values)

    @http.route('/cuentas_analiticas/get_employee_email', type='json', auth='public', website=True, csrf=False)
    def get_employee_email(self, partner_id):
        """Obtiene el email del empleado asociado al partner"""
        try:
            email = ''
            
            if partner_id:
                # Convertir a entero si viene como string
                partner_id = int(partner_id)
                
                # Buscar el empleado que tiene este partner como work_contact_id
                employee = request.env['hr.employee'].sudo().search([
                    ('work_contact_id', '=', partner_id)
                ], limit=1)
                
                if employee:
                    email = employee.work_email or ''
                    # Log para debugging
                    request.env['ir.logging'].sudo().create({
                        'name': 'Get Employee Email Success',
                        'type': 'server',
                        'level': 'info',
                        'message': f'Partner ID: {partner_id}, Employee: {employee.name}, Email: {email}',
                        'path': 'analytic_account_request',
                        'func': 'get_employee_email',
                        'line': '0',
                    })
                else:
                    # Log cuando no se encuentra empleado
                    request.env['ir.logging'].sudo().create({
                        'name': 'Get Employee Email - No Employee Found',
                        'type': 'server',
                        'level': 'warning',
                        'message': f'No se encontró empleado con work_contact_id: {partner_id}',
                        'path': 'analytic_account_request',
                        'func': 'get_employee_email',
                        'line': '0',
                    })
            
            return {'email': email}
        
        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Get Employee Email Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al obtener email para partner_id {partner_id}: {str(e)}',
                'path': 'analytic_account_request',
                'func': 'get_employee_email',
                'line': '0',
            })
            return {'email': '', 'error': str(e)}


    @http.route('/cuentas_analiticas/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_request(self, **post):
        """Procesa el envío del formulario"""
        try:
            # Validar datos requeridos
            required_fields = ['partner_id', 'company_id', 'plan_id', 'analytic_account_name']
            for field in required_fields:
                if not post.get(field):
                    return request.redirect('/cuentas_analiticas/formulario?error=Todos los campos obligatorios deben ser completados')

            # Obtener datos del partner/empleado
            partner_id = int(post.get('partner_id'))
            partner = request.env['res.partner'].sudo().browse(partner_id)
            
            if not partner.exists():
                return request.redirect('/cuentas_analiticas/formulario?error=El solicitante seleccionado no es válido')
            
            # Buscar el empleado asociado
            employee = request.env['hr.employee'].sudo().search([
                ('work_contact_id', '=', partner_id)
            ], limit=1)
            
            if not employee:
                return request.redirect('/cuentas_analiticas/formulario?error=No se encontró un empleado asociado al solicitante')
            
            if not employee.work_email:
                return request.redirect('/cuentas_analiticas/formulario?error=El empleado no tiene un correo electrónico configurado')

            # Crear la solicitud
            request_vals = {
                'partner_id': partner_id,
                'company_id': int(post.get('company_id')),
                'plan_id': int(post.get('plan_id')),
                'analytic_account_name': post.get('analytic_account_name'),
                'observations': post.get('observations', ''),
                'state': 'draft',
            }
            
            # Crear el registro
            analytic_request = request.env['analytic.account.request'].sudo().create(request_vals)
            
            # Enviar la solicitud (cambiar a estado 'requested' y enviar emails)
            analytic_request.action_submit()
            
            # Redireccionar con mensaje de éxito
            return request.redirect(
                f'/cuentas_analiticas/formulario?success=Tu solicitud fue procesada con el número {analytic_request.name}. '
                f'Recibirás un correo electrónico de confirmación en {employee.work_email}'
                f'&request_number={analytic_request.name}'
            )

        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Analytic Account Request Submission Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al procesar solicitud: {str(e)}',
                'path': 'analytic_account_request',
                'func': 'submit_request',
                'line': '0',
            })
            return request.redirect(f'/cuentas_analiticas/formulario?error=Error al procesar la solicitud: {str(e)}')


class CreditCardRequestController(http.Controller):

    @http.route('/tarjeta_credito/formulario', type='http', auth='public', website=True, csrf=False)
    def credit_card_form(self, **kwargs):
        """Muestra el formulario de solicitud de tarjeta de crédito"""
        
        # Obtener partners disponibles (asociados a empleados)
        employees = request.env['hr.employee'].sudo().search([('active', '=', True)])
        partners = employees.mapped('work_contact_id')
        
        # Obtener compañías
        companies = request.env['res.company'].sudo().search([])
        
        # Fecha actual
        today = fields.Date.context_today(request.env['credit.card.request'])
        
        values = {
            'partners': partners,
            'companies': companies,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
            'request_number': kwargs.get('request_number', ''),
        }
        return request.render('analytic_account_request.credit_card_request_form_template', values)


class ProductRequestController(http.Controller):

    @http.route('/producto/formulario', type='http', auth='public', website=True, csrf=False)
    def product_form(self, **kwargs):
        """Muestra el formulario de solicitud de creación de producto"""
        
        # Obtener partners disponibles (asociados a empleados)
        employees = request.env['hr.employee'].sudo().search([('active', '=', True)])
        partners = employees.mapped('work_contact_id')
        
        # Obtener compañías
        companies = request.env['res.company'].sudo().search([])
        
        # Fecha actual
        today = fields.Date.context_today(request.env['product.request'])
        
        values = {
            'partners': partners,
            'companies': companies,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
            'request_number': kwargs.get('request_number', ''),
        }
        return request.render('analytic_account_request.product_request_form_template', values)
    
    @http.route('/producto/get_analytic_accounts', type='json', auth='public', website=True, csrf=False)
    def get_analytic_accounts(self, company_id):
        """Obtiene las cuentas analíticas de una compañía"""
        try:
            analytic_accounts = []
            
            if company_id:
                # Convertir a entero si viene como string
                company_id = int(company_id)
                
                # Buscar cuentas analíticas de la compañía
                accounts = request.env['account.analytic.account'].sudo().search([
                    ('company_id', '=', company_id)
                ])
                
                analytic_accounts = [{'id': acc.id, 'name': acc.name} for acc in accounts]
                
                # Log para debugging
                request.env['ir.logging'].sudo().create({
                    'name': 'Get Analytic Accounts Success',
                    'type': 'server',
                    'level': 'info',
                    'message': f'Company ID: {company_id}, Found {len(analytic_accounts)} accounts',
                    'path': 'product.request',
                    'func': 'get_analytic_accounts',
                    'line': '0',
                })
            
            return {'accounts': analytic_accounts}
        
        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Get Analytic Accounts Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al obtener cuentas analíticas para company_id {company_id}: {str(e)}',
                'path': 'product.request',
                'func': 'get_analytic_accounts',
                'line': '0',
            })
            return {'accounts': [], 'error': str(e)}
    
    @http.route('/producto/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_product_request(self, **post):
        """Procesa el envío del formulario de producto"""
        try:
            # Validar datos requeridos
            required_fields = [
                'partner_id', 'company_id', 'product_type', 'product_name',
                'product_justification', 'disclosure_medium', 'has_variants',
                'analytic_account_id', 'payment_method', 'policy_responsible'
            ]
            for field in required_fields:
                if not post.get(field):
                    return request.redirect('/producto/formulario?error=Todos los campos obligatorios deben ser completados')
            
            # Manejar archivo de variantes si se subió
            variants_file = False
            variants_filename = False
            if post.get('variants_file'):
                import base64
                variants_file = base64.b64encode(post.get('variants_file').read())
                variants_filename = post.get('variants_file').filename
            
            # Preparar valores para crear la solicitud
            vals = {
                'requester_partner_id': int(post.get('partner_id')),
                'company_id': int(post.get('company_id')),
                'product_type': post.get('product_type'),
                'product_name': post.get('product_name'),
                'product_justification': post.get('product_justification'),
                'disclosure_medium': post.get('disclosure_medium'),
                'has_variants': post.get('has_variants'),
                'variants_file': variants_file,
                'variants_filename': variants_filename,
                'analytic_account_id': int(post.get('analytic_account_id')),
                'is_deferred': post.get('is_deferred') == 'true',
                'deferred_time': int(post.get('deferred_time', 0)) if post.get('deferred_time') else 0,
                'payment_method': post.get('payment_method'),
                'policy_responsible': post.get('policy_responsible'),
                # Aspectos legales
                'legal_purpose': post.get('legal_purpose', ''),
                'specific_objectives': post.get('specific_objectives', ''),
                'scope': post.get('scope', ''),
                'duration': post.get('duration', ''),
                'place': post.get('place', ''),
                'price': post.get('price', ''),
                'logyca_obligations': post.get('logyca_obligations', ''),
                'acceptor_obligations': post.get('acceptor_obligations', ''),
                'termination_causes': post.get('termination_causes', ''),
                'liquidation_method': post.get('liquidation_method', ''),
                'contract_assignment': post.get('contract_assignment', ''),
                'penalty_clause': post.get('penalty_clause', ''),
                'observations': post.get('observations', ''),
            }
            
            # Crear la solicitud
            product_request = request.env['product.request'].sudo().create(vals)
            
            # Enviar la solicitud (cambia a estado 'requested' y envía emails)
            product_request.action_submit()
            
            # Log de éxito
            request.env['ir.logging'].sudo().create({
                'name': 'Product Request Created',
                'type': 'server',
                'level': 'info',
                'message': f'Solicitud creada: {product_request.name}',
                'path': 'product.request',
                'func': 'submit_product_request',
                'line': '0',
            })
            
            # Redirigir con mensaje de éxito
            return request.redirect(f'/producto/formulario?success=true&request_number={product_request.name}')
        
        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Product Request Submission Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al crear solicitud: {str(e)}',
                'path': 'product.request',
                'func': 'submit_product_request',
                'line': '0',
            })
            return request.redirect(f'/producto/formulario?error=Error al procesar la solicitud: {str(e)}')


class CreditCardRequestController(http.Controller):

    @http.route('/tarjeta_credito/formulario', type='http', auth='public', website=True, csrf=False)
    def credit_card_form(self, **kwargs):
        """Muestra el formulario de solicitud de tarjeta de crédito"""
        
        # Obtener partners disponibles (asociados a empleados)
        employees = request.env['hr.employee'].sudo().search([('active', '=', True)])
        partners = employees.mapped('work_contact_id')
        
        # Obtener compañías
        companies = request.env['res.company'].sudo().search([])
        
        # Obtener todos los departamentos (para tenerlos como fallback)
        departments = request.env['hr.department'].sudo().search([])
        
        # Fecha actual
        today = fields.Date.context_today(request.env['credit.card.request'])
        
        values = {
            'partners': partners,
            'companies': companies,
            'departments': departments,
            'today': today,
            'error': kwargs.get('error', ''),
            'success': kwargs.get('success', ''),
            'request_number': kwargs.get('request_number', ''),
        }
        return request.render('analytic_account_request.credit_card_form_template', values)

    @http.route('/tarjeta_credito/get_employee_data', type='json', auth='public', website=True, csrf=False)
    def get_employee_data(self, partner_id, data_type='email'):
        """Obtiene datos del empleado asociado al partner"""
        try:
            result = {'success': False}
            
            if partner_id:
                # Convertir a entero si viene como string
                partner_id = int(partner_id)
                
                # Buscar el empleado que tiene este partner como work_contact_id
                employee = request.env['hr.employee'].sudo().search([
                    ('work_contact_id', '=', partner_id)
                ], limit=1)
                
                if employee:
                    if data_type == 'email':
                        result = {
                            'success': True,
                            'email': employee.work_email or ''
                        }
                    elif data_type == 'job':
                        result = {
                            'success': True,
                            'job_id': employee.job_id.id if employee.job_id else False,
                            'job_name': employee.job_id.name if employee.job_id else ''
                        }
                    elif data_type == 'identification':
                        result = {
                            'success': True,
                            'identification': employee.identification_id or ''
                        }
            
            return result
        
        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Get Employee Data Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al obtener datos del empleado para partner_id {partner_id}: {str(e)}',
                'path': 'credit_card_request',
                'func': 'get_employee_data',
                'line': '0',
            })
            return {'success': False, 'error': str(e)}

    @http.route('/tarjeta_credito/get_departments', type='json', auth='public', website=True, csrf=False)
    def get_departments(self, company_id):
        """Obtiene los departamentos de una compañía"""
        try:
            departments_data = []
            
            # Log de entrada
            request.env['ir.logging'].sudo().create({
                'name': 'Get Departments - Start',
                'type': 'server',
                'level': 'info',
                'message': f'Buscando departamentos para company_id: {company_id}',
                'path': 'credit_card_request',
                'func': 'get_departments',
                'line': '0',
            })
            
            if company_id:
                company_id = int(company_id)
                
                # Buscar departamentos de la compañía
                # Incluimos también departamentos sin compañía asignada para mayor flexibilidad
                departments = request.env['hr.department'].sudo().search([
                    '|',
                    ('company_id', '=', company_id),
                    ('company_id', '=', False)
                ])
                
                departments_data = [{'id': d.id, 'name': d.name} for d in departments]
                
                # Log de resultado
                request.env['ir.logging'].sudo().create({
                    'name': 'Get Departments - Success',
                    'type': 'server',
                    'level': 'info',
                    'message': f'Encontrados {len(departments_data)} departamentos para company_id {company_id}',
                    'path': 'credit_card_request',
                    'func': 'get_departments',
                    'line': '0',
                })
            
            return {'success': True, 'departments': departments_data}
        
        except Exception as e:
            request.env['ir.logging'].sudo().create({
                'name': 'Get Departments Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error obteniendo departamentos: {str(e)}',
                'path': 'credit_card_request',
                'func': 'get_departments',
                'line': '0',
            })
            return {'success': False, 'error': str(e)}

    @http.route('/tarjeta_credito/submit', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def submit_credit_card_request(self, **post):
        """Procesa el envío del formulario de tarjeta de crédito"""
        try:
            # Validar datos requeridos
            required_fields = ['requester_partner_id', 'cardholder_partner_id', 
                             'cardholder_identification', 'company_id', 'department_id']
            for field in required_fields:
                if not post.get(field):
                    return request.redirect('/tarjeta_credito/formulario?error=Todos los campos obligatorios deben ser completados')

            # Obtener datos del solicitante
            requester_partner_id = int(post.get('requester_partner_id'))
            requester_partner = request.env['res.partner'].sudo().browse(requester_partner_id)
            
            if not requester_partner.exists():
                return request.redirect('/tarjeta_credito/formulario?error=El solicitante seleccionado no es válido')
            
            # Buscar el empleado asociado al solicitante
            requester_employee = request.env['hr.employee'].sudo().search([
                ('work_contact_id', '=', requester_partner_id)
            ], limit=1)
            
            if not requester_employee:
                return request.redirect('/tarjeta_credito/formulario?error=No se encontró un empleado asociado al solicitante')
            
            if not requester_employee.work_email:
                return request.redirect('/tarjeta_credito/formulario?error=El solicitante no tiene un correo electrónico configurado')

            # Validar tarjetahabiente
            cardholder_partner_id = int(post.get('cardholder_partner_id'))
            cardholder_partner = request.env['res.partner'].sudo().browse(cardholder_partner_id)
            
            if not cardholder_partner.exists():
                return request.redirect('/tarjeta_credito/formulario?error=El tarjetahabiente seleccionado no es válido')

            # Crear la solicitud
            request_vals = {
                'requester_partner_id': requester_partner_id,
                'cardholder_partner_id': cardholder_partner_id,
                'cardholder_identification': post.get('cardholder_identification'),
                'company_id': int(post.get('company_id')),
                'department_id': int(post.get('department_id')),
                'state': 'draft',
            }
            
            # Crear el registro
            credit_card_request = request.env['credit.card.request'].sudo().create(request_vals)
            
            # Enviar la solicitud (cambiar a estado 'requested' y enviar emails)
            credit_card_request.action_submit()
            
            # Redireccionar con mensaje de éxito
            return request.redirect(
                f'/tarjeta_credito/formulario?success=Tu solicitud fue procesada con el número {credit_card_request.name}. '
                f'Recibirás un correo electrónico de confirmación en {requester_employee.work_email}'
                f'&request_number={credit_card_request.name}'
            )

        except Exception as e:
            # Log del error
            request.env['ir.logging'].sudo().create({
                'name': 'Credit Card Request Submission Error',
                'type': 'server',
                'level': 'error',
                'message': f'Error al procesar solicitud: {str(e)}',
                'path': 'credit_card_request',
                'func': 'submit_credit_card_request',
                'line': '0',
            })
            return request.redirect(f'/tarjeta_credito/formulario?error=Error al procesar la solicitud: {str(e)}')
