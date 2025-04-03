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

        if not postulation_ids:
            return request.not_found()

        postulation_id = postulation_ids[0]
        _logger.info("Procesando postulación ID: %s, Estado actual: %s",
                    postulation_id.id, postulation_id.state)

        if postulation_id.state == "done":
            return request.render(
                "rvc.rvc_benefit_already_delivered",
                {"benefit_application": postulation_id, "token": token},
            )

        # Crear una clave única para la sesión
        session_key = f"rvc_benefit_processed_{token}"
        already_processed = session_key in request.session

        _logger.info("Clave de sesión: %s, ¿Ya procesado?: %s", session_key, already_processed)

        # Si el estado es "notified" y no ha sido procesado
        if postulation_id.state == "notified" and not already_processed:
            try:
                postulation_id.write(
                    {"state": "confirm", "acceptance_date": datetime.now()}
                )

                message = _(
                    f"{postulation_id.partner_id.partner_id.name} "
                    "<u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico."
                )
                postulation_id.message_post(body=message)

                postulation_id.attach_OM_2_partner(postulation_id)

                if postulation_id.product_id.benefit_type == "colabora":
                    postulation_id.calculate_end_date_colabora()

                # Marcar como procesado
                request.session[session_key] = True
                _logger.info("Marcado como procesado en sesión: %s", session_key)

            except Exception as e:
                _logger.error("Error al procesar el beneficio: %s", str(e))

        # Independientemente de procesamiento o errores, renderizar vista apropiada
        # Recargar registro para tener datos actualizados
        postulation_id.invalidate_cache()
        postulation_id = request.env["benefit.application"].sudo().browse(postulation_id.id)

        # Preparar fecha formateada
        tz = timezone("America/Bogota")
        formatted_date = postulation_id.acceptance_date.astimezone(tz).strftime(
            "%d/%m/%Y a las %H:%M"
        ) if postulation_id.acceptance_date else "N/A"

        if postulation_id.state in ["cancel", "rejected"]:
            _logger.info("Renderizando vista de error por estado %s", postulation_id.state)
            return request.render(
                "rvc.rvc_error_page",
                {
                    "benefit_application": postulation_id,
                    "token": token
                }
            )

        # Determinar qué vista renderizar basado en el estado y si ya fue procesado
        if postulation_id.state == "confirm":
            if already_processed:
                _logger.info("Renderizando vista de 'ya aceptado' (visita posterior)")
                return request.render(
                    "rvc.notify_rvc_benefit_already_accepted",
                    {
                        "benefit_application": postulation_id,
                        "token": token,
                        "formatted_acceptance_date": formatted_date
                    },
                )

        # Si llegamos aquí, es un estado diferente (probablemente "notified")
        _logger.info("Renderizando vista estándar para estado: %s", postulation_id.state)
        return request.render(
            "rvc.accept_rvc_benefit_page_view",
            {
                "benefit_application": postulation_id,
                "token": token,
                "formatted_acceptance_date": formatted_date,
                "already_processed": already_processed
            },
        )
