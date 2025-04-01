# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from logging import getLogger
from pytz import timezone
from datetime import datetime
import psycopg2
import time

_logger = getLogger(__name__)

class AcceptRvcBenefit(http.Controller):
    BOG_TIMEZONE = timezone('America/Bogota')
    MAX_RETRIES = 5
    RETRY_DELAY = 0.2  # segundos

    @http.route(
        "/rvc/accept_benefit/<string:token>", type="http", auth="public", website=True
    )
    def accept_benefit(self, token, **kwargs):
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._process_benefit_acceptance(token, attempt)
            except psycopg2.errors.SerializationFailure as e:
                self._handle_serialization_error(attempt, e)
            except Exception as e:
                return self._handle_general_error(e)

        # Si llegamos aquí es porque agotamos los reintentos
        _logger.error(
            "Se agotaron los %d reintentos para procesar el token %s",
            self.MAX_RETRIES,
            token
        )
        return self._render_service_unavailable()

    def _process_benefit_acceptance(self, token, attempt):
        """Procesa la solicitud de aceptación de beneficio"""
        postulation_ids = self._get_benefit_applications(token)

        if not postulation_ids:
            return request.not_found()

        for postulation in postulation_ids:
            _logger.info(
                "Intento %d/%d - Estado: %s",
                attempt + 1,
                self.MAX_RETRIES,
                postulation.state
            )
            self._set_lang_context(postulation)

            # Manejar según el estado actual
            if postulation.state == "done":
                return self._handle_done_state(postulation, token)

            if postulation.state == "confirm":
                return self._handle_confirm_state(postulation, token)

            if postulation.state == "notified":
                return self._handle_notified_state(postulation, token)

        # Si llegamos aquí sin retornar, es que algo no encaja con los estados esperados
        _logger.warning("Estado no manejado en benefit application: %s", postulation.state)
        return request.redirect('/')

    def _get_benefit_applications(self, token):
        """Obtiene las solicitudes de beneficio según el token"""
        return (
            request.env["benefit.application"]
            .sudo()
            .with_for_update()
            .search([("access_token", "=", token)])
        )

    def _set_lang_context(self, postulation):
        """Configura el contexto del idioma basado en el socio"""
        lang = postulation.partner_id.partner_id.lang or 'es_ES'
        request.context = dict(request.context, lang=lang)

    def _handle_done_state(self, postulation, token):
        """Maneja el estado 'done' de la solicitud"""
        return request.render(
            'rvc.rvc_benefit_already_delivered',
            {"benefit_application": postulation, "token": token}
        )

    def _handle_confirm_state(self, postulation, token):
        """Maneja el estado 'confirm' de la solicitud"""
        formatted_date = postulation.acceptance_date\
            .astimezone(self.BOG_TIMEZONE)\
            .strftime('%d/%m/%Y a las %H:%M')

        return request.render(
            'rvc.notify_rvc_benefit_already_accepted',
            {
                "benefit_application": postulation,
                "token": token,
                'formatted_acceptance_date': formatted_date
            }
        )

    def _handle_notified_state(self, postulation, token):
        """Maneja el estado 'notified' de la solicitud"""
        # Verificamos que el estado no haya cambiado
        fresh_state = self._get_fresh_state(postulation.id)
        if fresh_state != "notified":
            _logger.warning("El estado cambió de notified a %s entre lecturas", fresh_state)
            return None  # Esto hará que se continúe con la siguiente iteración

        self._confirm_benefit_acceptance(postulation)
        return request.render(
            'rvc.accept_rvc_benefit_page_view',
            {"benefit_application": postulation, "token": token}
        )

    def _get_fresh_state(self, postulation_id):
        """Obtiene el estado actual de la solicitud para evitar condiciones de carrera"""
        return request.env["benefit.application"].sudo().browse(postulation_id).state

    def _confirm_benefit_acceptance(self, postulation):
        """Confirma la aceptación del beneficio"""
        postulation.write({
            "state": "confirm",
            "acceptance_date": datetime.now()
        })

        self._post_acceptance_message(postulation)
        postulation.attach_OM_2_partner(postulation)

        if postulation.product_id.benefit_type == "colabora":
            postulation.calculate_end_date_colabora()

    def _post_acceptance_message(self, postulation):
        """Publica mensaje de aceptación en el muro de la solicitud"""
        message = _(
            f"{postulation.partner_id.partner_id.name} "
            "<u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico."
        )
        postulation.message_post(body=message)

    def _handle_serialization_error(self, attempt, exception):
        """Maneja errores de serialización en la base de datos"""
        _logger.warning(
            "Retry %d/%d debido a error de serialización: %s", 
            attempt + 1, 
            self.MAX_RETRIES, 
            exception
        )
        request.env.cr.rollback()
        time.sleep(self.RETRY_DELAY)

    def _handle_general_error(self, exception):
        """Maneja errores generales"""
        _logger.error(
            "Error no manejado en la aceptación del beneficio: %s",
            str(exception),
            exc_info=True
        )
        # Reemplazamos la plantilla website.http_error con una respuesta más simple
        return request.render('rvc.rvc_error_page', {
            'error_title': _('Error interno del servidor'),
            'error_message': _('Ha ocurrido un error. Por favor, inténtelo más tarde o contacte a soporte.')
        }, status=500)

    def _render_service_unavailable(self):
        """Muestra página de servicio no disponible"""
        return request.render('rvc.rvc_error_page', {
            'error_title': _('Servicio no disponible'),
            'error_message': _('Servicio temporalmente no disponible. Por favor, intente más tarde.')
        }, status=503)
