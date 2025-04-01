# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from datetime import datetime
import logging
from pytz import timezone

_logger = logging.getLogger(__name__)

class AcceptRvcBenefit(http.Controller):

    @http.route(
        "/rvc/accept_benefit/<string:token>", type="http", auth="public", website=True
    )
    def accept_benefit(self, token, **kwargs):
        # Usamos cr.execute directamente para bloquear la fila para esta transacción
        request.env.cr.execute("""
            SELECT id, state, acceptance_date FROM benefit_application 
            WHERE access_token = %s FOR UPDATE
        """, (token,))
        result = request.env.cr.dictfetchone()

        if not result:
            return request.not_found()

        postulation_id = request.env['benefit.application'].sudo().browse(result['id'])
        _logger.info("Procesando beneficio con estado: %s", postulation_id.state)

        # Configurar contexto del idioma
        lang = postulation_id.partner_id.partner_id.lang or 'es_ES'
        request.context = dict(request.context, lang=lang)

        # Beneficio ya entregado
        if postulation_id.state == "done":
            return request.render(
                'rvc.rvc_benefit_already_delivered',
                {"benefit_application": postulation_id, "token": token}
            )

        # Beneficio ya aceptado previamente
        if postulation_id.state == "confirm" and postulation_id.acceptance_date:
            # Formatear la fecha de aceptación
            tz = timezone('America/Bogota')
            formatted_date = (postulation_id.acceptance_date
                            .astimezone(tz)
                            .strftime('%d/%m/%Y a las %H:%M'))

            return request.render(
                'rvc.notify_rvc_benefit_already_accepted',
                {
                    "benefit_application": postulation_id, 
                    "token": token,
                    "formatted_acceptance_date": formatted_date
                }
            )

        # Primera aceptación del beneficio
        if postulation_id.state == "notified" and postulation_id.acceptance_date is False:
            # Cambiar estado ANTES de procesar cualquier operación
            postulation_id.write({
                "state": "confirm", 
                "acceptance_date": datetime.now()
            })

            # Registrar en el historial
            message = _(
                f"{postulation_id.partner_id.partner_id.name} "
                "<u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico."
            )
            postulation_id.message_post(body=message)

            # Procesar adjuntos y fechas
            postulation_id.attach_OM_2_partner(postulation_id)

            if postulation_id.product_id.benefit_type == "colabora":
                postulation_id.calculate_end_date_colabora()

            # Mostrar página de aceptación exitosa
            return request.render(
                'rvc.accept_rvc_benefit_page_view',
                {"benefit_application": postulation_id, "token": token}
            )

        # Estado no reconocido
        return request.redirect('/')
