# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from logging import getLogger
from pytz import timezone
from datetime import datetime

_logger = getLogger(__name__)

class AcceptRvcBenefit(http.Controller):

    @http.route(
        "/rvc/accept_benefit/<string:token>", type="http", auth="public", website=True
    )
    def accept_benefit(self, token, **kwargs):
        postulation_ids = (
            request.env["benefit.application"]
            .sudo()
            .with_for_update()  # bloquear fila para evitar que se procese varias veces
            .search([("access_token", "=", token)])
        )
        if not postulation_ids:
            return request.not_found()

        for postulation_id in postulation_ids:
            _logger.info("Estado inicial: %s", postulation_id.state)
            lang = postulation_id.partner_id.partner_id.lang or 'es_ES'
            request.context = dict(request.context, lang=lang)

            if postulation_id.state == "done":
                return request.render(
                    'rvc.rvc_benefit_already_delivered',
                    {"benefit_application": postulation_id, "token": token}
                )

            if postulation_id.state == "confirm":
                tz = timezone('America/Bogota')
                formatted_date = postulation_id.acceptance_date\
                    .astimezone(tz)\
                    .strftime('%d/%m/%Y a las %H:%M')

                return request.render(
                    'rvc.notify_rvc_benefit_already_accepted',
                    {
                        "benefit_application": postulation_id,
                        "token": token,
                        'formatted_acceptance_date': formatted_date
                    }
                )

            if postulation_id.state == "notified":
                postulation_id.write(
                    {"state": "confirm", "acceptance_date": datetime.now()}
                )
                message = _(
                    f"{postulation_id.partner_id.partner_id.name} "
                    "<u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico."
                )
                postulation_id.message_post(body=message)

                # agregando adjunto al tercero
                postulation_id.attach_OM_2_partner(postulation_id)

                if postulation_id.product_id.benefit_type == "colabora":
                    postulation_id.calculate_end_date_colabora()

                return request.render(
                    'rvc.accept_rvc_benefit_page_view',
                    {"benefit_application": postulation_id, "token": token}
                )
