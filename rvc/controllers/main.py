# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from pytz import timezone
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class AcceptRvcBenefit(http.Controller):

    @http.route(
        ["/rvc/accept_benefit/<string:token>"], type="http", auth="public", website=True
    )
    def accept_benefit(self, token, **kwargs):
        _logger.info("=== INICIANDO accept_benefit con token: %s ===", token)

        postulation_ids = (
            request.env["benefit.application"]
            .sudo()
            .search([("access_token", "=", token)])
        )

        _logger.info("Postulaciones encontradas: %s", len(postulation_ids))

        if not postulation_ids:
            _logger.warning("No se encontraron postulaciones con el token: %s", token)
            return request.not_found()

        for postulation_id in postulation_ids:
            _logger.info("Procesando postulación ID: %s, Estado actual: %s", 
                        postulation_id.id, postulation_id.state)

            if postulation_id.state == "done":
                _logger.info(
                    "La postulación ya está completada (estado: done), "
                    "renderizando vista 'already_delivered'"
                )
                return request.render(
                    "rvc.rvc_benefit_already_delivered",
                    {"benefit_application": postulation_id, "token": token},
                )

            # Crear una clave única para la sesión
            session_key = f"rvc_benefit_processed_{token}"
            already_processed = session_key in request.session

            _logger.info("Clave de sesión: %s, ¿Ya procesado?: %s", session_key, already_processed)
            _logger.info("Claves actuales en sesión: %s", list(request.session.keys()))

            # Si el estado es "notified" y no ha sido procesado
            if postulation_id.state == "notified" and not already_processed:
                _logger.info("ACTUALIZANDO postulación a estado 'confirm' (primera vez)")

                postulation_id.write(
                    {"state": "confirm", "acceptance_date": datetime.now()}
                )
                message = _(
                    f"{postulation_id.partner_id.partner_id.name} "
                    "<u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico."
                )
                postulation_id.message_post(body=message)
                _logger.info("Mensaje publicado en el chatter")

                _logger.info("Ejecutando attach_OM_2_partner")
                postulation_id.attach_OM_2_partner(postulation_id)

                if postulation_id.product_id.benefit_type == "colabora":
                    _logger.info("Calculando fecha fin para beneficio tipo 'colabora'")
                    postulation_id.calculate_end_date_colabora()

                # Marcar como procesado en la sesión
                request.session[session_key] = True
                _logger.info("Marcado como procesado en sesión: %s", session_key)

            # Preparar respuesta
            tz = timezone("America/Bogota")
            formatted_date = postulation_id.acceptance_date.astimezone(tz).strftime(
                "%d/%m/%Y a las %H:%M"
            ) if postulation_id.acceptance_date else "N/A"

            _logger.info("Fecha formateada: %s", formatted_date)

            if postulation_id.state == "confirm":
                view_to_render = (
                    "rvc.accept_rvc_benefit_page_view" 
                    if not already_processed 
                    else "rvc.notify_rvc_benefit_already_accepted"
                )
                _logger.info("Renderizando vista: %s (¿Primera vez?: %s)",
                            view_to_render, not already_processed)

                return request.render(
                    view_to_render,
                    {
                        "benefit_application": postulation_id,
                        "token": token,
                        "formatted_acceptance_date": formatted_date,
                    },
                )
            _logger.warning("Estado inesperado: %s, no se renderiza ninguna vista específica",
                              postulation_id.state)

        _logger.warning("No se procesó ninguna postulación correctamente, retornando not_found")
        return request.not_found()
