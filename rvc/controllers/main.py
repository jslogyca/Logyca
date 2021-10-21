# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from datetime import datetime

class AcceptRvcBenefit(http.Controller):

    @http.route('/rvc/accept_benefit/<string:token>', type='http', auth="public", website=True)
    def accept_benefit(self, token, **kwargs):
        postulation_ids = request.env['benefit.application'].sudo().search([('access_token', '=', token)])
        if not postulation_ids:
            return request.not_found()

        for postulation_id in postulation_ids:

            # Marcar la posituación como aceptada
            if postulation_id.state == 'notified':
                postulation_id.write({'state': 'confirm', 'acceptance_date': datetime.now()})
                postulation_id.message_post(body=_(\
                    '%s <u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico.' % str(postulation_id.partner_id.partner_id.name)))

                #agregando adjunto al tercero
                postulation_id.attach_OM_2_partner(postulation_id)

                if postulation_id.product_id.benefit_type == 'colabora':
                    postulation_id.calculate_end_date_colabora()

                lang = postulation_id.partner_id.partner_id.lang
                return request.env['ir.ui.view'].with_context(lang=lang).render_template('rvc.accept_rvc_benefit_page_view', {
                    'benefit_application': postulation_id, 'token': token
                })
