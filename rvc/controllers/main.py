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
    def accept_benefit(self, token, processed=None, **kwargs):
        postulation_ids = (
            request.env["benefit.application"]
            .sudo()
            .search([("access_token", "=", token)])
        )

        if not postulation_ids:
            return request.not_found()

        for postulation_id in postulation_ids:
            if postulation_id.state == "done":
                return request.render(
                    "rvc.rvc_benefit_already_delivered",
                    {"benefit_application": postulation_id, "token": token},
                )

            # Si el estado es "notified" y no ha sido procesado aún
            if postulation_id.state == "notified" and not processed:
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

                # Redirigir con el parámetro processed para evitar el doble procesamiento
                return request.redirect(f"/rvc/accept_benefit/{token}?processed=1")

            # Este bloque se ejecutará después de la redirección o si ya estaba en estado "confirm"
            if postulation_id.state == "confirm":
                tz = timezone("America/Bogota")
                formatted_date = postulation_id.acceptance_date.astimezone(tz).strftime(
                    "%d/%m/%Y a las %H:%M"
                )

                return request.render(
                    "rvc.notify_rvc_benefit_already_accepted",
                    {
                        "benefit_application": postulation_id,
                        "token": token,
                        "formatted_acceptance_date": formatted_date,
                    },
                )

        return request.not_found()
