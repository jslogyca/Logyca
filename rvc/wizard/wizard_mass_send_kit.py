from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WizardMassSendKit(models.TransientModel):
    _name = 'wizard.mass.send.kit'
    _description = 'Asistente para Envío Masivo de Kit de Bienvenida'

    postulacion_ids = fields.Many2many(
        'benefit.application',
        string='Postulaciones Seleccionadas',
        readonly=True
    )
    
    total_seleccionadas = fields.Integer(
        string='Total Seleccionadas',
        compute='_compute_totales',
        store=True
    )
    
    postulaciones_validas = fields.Integer(
        string='En Estado Confirmado',
        compute='_compute_totales',
        store=True
    )
    
    postulaciones_invalidas = fields.Integer(
        string='En Otros Estados',
        compute='_compute_totales',
        store=True
    )
    
    mensaje_validacion = fields.Html(
        string='Resumen',
        compute='_compute_mensaje_validacion'
    )
    
    resultado_envio = fields.Html(
        string='Resultado del Envío',
        readonly=True
    )
    
    mostrar_resultado = fields.Boolean(
        string='Mostrar Resultado',
        default=False
    )

    @api.depends('postulacion_ids')
    def _compute_totales(self):
        for wizard in self:
            wizard.total_seleccionadas = len(wizard.postulacion_ids)
            wizard.postulaciones_validas = len(
                wizard.postulacion_ids.filtered(lambda p: p.state == 'confirm')
            )
            wizard.postulaciones_invalidas = (
                wizard.total_seleccionadas - wizard.postulaciones_validas
            )

    @api.depends('postulacion_ids', 'postulaciones_validas', 'postulaciones_invalidas')
    def _compute_mensaje_validacion(self):
        for wizard in self:
            if not wizard.postulacion_ids:
                wizard.mensaje_validacion = """
                    <div class="alert alert-warning" role="alert">
                        <h4>⚠️ No hay postulaciones seleccionadas</h4>
                        <p>Debe seleccionar al menos una postulación desde la vista de lista.</p>
                    </div>
                """
                continue
            
            validas = wizard.postulaciones_validas
            invalidas = wizard.postulaciones_invalidas
            
            html = "<div style='padding: 10px;'>"
            
            # Resumen general
            html += f"""
                <div class="alert alert-info" role="alert">
                    <h4>📊 Resumen de Postulaciones</h4>
                    <ul style="margin: 10px 0;">
                        <li><strong>Total seleccionadas:</strong> {wizard.total_seleccionadas}</li>
                        <li style="color: green;"><strong>En estado 'Confirmado':</strong> {validas}</li>
                        <li style="color: orange;"><strong>En otros estados:</strong> {invalidas}</li>
                    </ul>
                </div>
            """
            
            # Advertencias
            if validas == 0:
                html += """
                    <div class="alert alert-danger" role="alert">
                        <h4>❌ No se puede continuar</h4>
                        <p>Ninguna de las postulaciones seleccionadas está en estado 'Confirmado'.</p>
                    </div>
                """
            elif invalidas > 0:
                html += f"""
                    <div class="alert alert-warning" role="alert">
                        <h4>⚠️ Atención</h4>
                        <p>{invalidas} postulación(es) será(n) omitida(s) por no estar en estado 'Confirmado'.</p>
                        <p>Solo se enviará el kit a las {validas} postulación(es) en estado válido.</p>
                    </div>
                """
            else:
                html += f"""
                    <div class="alert alert-success" role="alert">
                        <h4>✓ Listo para enviar</h4>
                        <p>Todas las postulaciones seleccionadas ({validas}) están en estado 'Confirmado'.</p>
                        <p>Se enviará el Kit de Bienvenida a todas ellas.</p>
                    </div>
                """
            
            # Información adicional
            html += """
                <div class="alert alert-light" role="alert">
                    <h5>ℹ️ ¿Qué sucederá al confirmar?</h5>
                    <ul>
                        <li>Se ejecutará la acción <strong>"Enviar Kit de Bienvenida"</strong></li>
                        <li>Las postulaciones cambiarán de estado según la configuración</li>
                        <li>Se registrarán los envíos en el sistema</li>
                        <li>Recibirá un reporte detallado de la operación</li>
                    </ul>
                </div>
            """
            
            html += "</div>"
            wizard.mensaje_validacion = html

    @api.model
    def default_get(self, fields_list):
        """Obtiene las postulaciones seleccionadas desde el contexto"""
        res = super().default_get(fields_list)
        
        postulacion_ids = self.env.context.get('active_ids', [])
        if postulacion_ids:
            res['postulacion_ids'] = [(6, 0, postulacion_ids)]
        
        return res

    def action_open_wizard(self):
        """Abre el wizard desde la server action"""
        return {
            'name': 'Envío Masivo de Kit de Bienvenida',
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.mass.send.kit',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_done(self, benefit_application):
        if benefit_application:
            if benefit_application.send_kit_with_no_benefit:
                benefit_application.message_post(body=_(\
                    '✅ Se entregó el beneficio RVC correctamente.'))
                return benefit_application.write({'state': 'done', 'delivery_date': datetime.now()})
            contact_email = benefit_application.partner_id.contact_email
            if contact_email:
                if benefit_application.product_id.benefit_type == 'codigos':
                    activated = self.env['rvc.activations'].activate_gs1_codes(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de Códigos GS1.'))
                elif benefit_application.product_id.benefit_type == 'colabora':
                    activated = self.env['rvc.activations'].activate_logyca_colabora(benefit_application)
                    if activated:
                        benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de la plataforma LOGYCA / COLABORA.'))
                    else:
                        benefit_application.message_post(body=_(\
                            '🚫 No se pudo <strong>solicitar la activación</strong></u> de la plataforma LOGYCA / COLABORA.'))
                elif benefit_application.product_id.benefit_type == 'tarjeta_digital':
                    if benefit_application.digital_card_ids:
                        activated = self.env['rvc.activations'].activate_digital_cards(benefit_application)
                        if activated:
                            benefit_application.message_post(body=_(\
                            '✅ Se solicitó la activación de Tarjetas Digitales.'))
                    else:
                        raise ValidationError(
                            _('¡Error! No hay tarjetas digitales para generar 😔.\n\nPara solicitarlas: \n'
                              '1. Active el modo edición yendo al botón EDITAR del lado superior izquierdo.\n'
                              '2. Vaya a la sección de Tarjetas Digitales.\n'
                              '3. Pulse la opción "Agregar línea."')
                        )
            else:
                raise ValidationError(_('La empresa seleccionada no tiene email.'))

        return {'type': 'ir.actions.act_window_close'}

    def action_confirmar_envio(self):
        """Ejecuta el envío masivo del kit de bienvenida"""
        self.ensure_one()
        
        # Filtrar postulaciones válidas
        postulaciones_validas = self.postulacion_ids.filtered(
            lambda p: p.state == 'confirm'
        )
        
        if not postulaciones_validas:
            raise UserError(
                "No hay postulaciones en estado 'Confirmado' para procesar."
            )
        
        # Ejecutar action_done para cada postulación
        exitosos = []
        errores = []
        
        for postulacion in postulaciones_validas:
            try:
                self.action_done(postulacion)
                exitosos.append(postulacion)
                _logger.info(
                    f"Kit enviado exitosamente para: {postulacion.partner_id.partner_id.name}"
                )
            except Exception as e:
                error_msg = str(e)
                errores.append({
                    'postulacion': postulacion,
                    'error': error_msg
                })
                _logger.error(
                    f"Error al enviar kit para {postulacion.partner_id.partner_id.name}: {error_msg}"
                )
        
        # Preparar resultado HTML
        resultado_html = self._generar_resultado_html(
            exitosos, 
            errores, 
            self.postulaciones_invalidas
        )
        
        # Actualizar wizard con resultado
        self.write({
            'resultado_envio': resultado_html,
            'mostrar_resultado': True
        })
        
        # Retornar la misma vista para mostrar resultados
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.mass.send.kit',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'show_result': True}
        }

    def _generar_resultado_html(self, exitosos, errores, omitidas):
        """Genera el HTML del resultado del envío"""
        html = "<div style='padding: 15px;'>"
        
        # Encabezado de resultado
        total_procesadas = len(exitosos) + len(errores)
        
        if len(errores) == 0 and omitidas == 0:
            html += """
                <div class="alert alert-success" role="alert">
                    <h3>✅ Envío Completado Exitosamente</h3>
                </div>
            """
        elif len(errores) == 0:
            html += """
                <div class="alert alert-success" role="alert">
                    <h3>✅ Envío Completado</h3>
                </div>
            """
        else:
            html += """
                <div class="alert alert-warning" role="alert">
                    <h3>⚠️ Envío Completado con Advertencias</h3>
                </div>
            """
        
        # Estadísticas
        html += f"""
            <div class="alert alert-info" role="alert">
                <h4>📊 Estadísticas del Proceso</h4>
                <table style="width: 100%; margin-top: 10px;">
                    <tr>
                        <td><strong>Kits enviados exitosamente:</strong></td>
                        <td style="color: green; font-weight: bold;">{len(exitosos)}</td>
                    </tr>
                    <tr>
                        <td><strong>Errores encontrados:</strong></td>
                        <td style="color: red; font-weight: bold;">{len(errores)}</td>
                    </tr>
                    <tr>
                        <td><strong>Postulaciones omitidas (estado incorrecto):</strong></td>
                        <td style="color: orange; font-weight: bold;">{omitidas}</td>
                    </tr>
                </table>
            </div>
        """
        
        # Lista de exitosos
        if exitosos:
            html += """
                <div class="alert alert-success" role="alert">
                    <h5>✓ Postulaciones Procesadas Exitosamente</h5>
                    <ul style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
            """
            for post in exitosos[:20]:  # Limitar a 20 para no sobrecargar
                html += f"<li>{post.partner_id.partner_id.name} - {post.name or 'N/A'}</li>"
            
            if len(exitosos) > 20:
                html += f"<li><em>... y {len(exitosos) - 20} más</em></li>"
            
            html += "</ul></div>"
        
        # Lista de errores
        if errores:
            html += """
                <div class="alert alert-danger" role="alert">
                    <h5>❌ Errores Encontrados</h5>
                    <ul style="margin-top: 10px; max-height: 200px; overflow-y: auto;">
            """
            for error in errores[:10]:  # Limitar a 10
                post = error['postulacion']
                msg = error['error']
                html += f"<li><strong>{post.partner_id.partner_id.name}:</strong> {msg}</li>"
            
            if len(errores) > 10:
                html += f"<li><em>... y {len(errores) - 10} errores más</em></li>"
            
            html += "</ul></div>"
        
        html += "</div>"
        return html

    def action_cerrar(self):
        """Cierra el wizard y actualiza la vista de postulaciones"""
        return {'type': 'ir.actions.act_window_close'}