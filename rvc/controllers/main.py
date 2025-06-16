# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang
from datetime import datetime

class AcceptRvcBenefit(http.Controller):

    @http.route('/rvc/accept_benefit/<string:token>', type='http', auth="public", website=True)
    def accept_benefit(self, token, **kwargs):
        postulation_id = request.env['benefit.application'].sudo().search([('access_token', '=', token)], limit=1)
        if not postulation_id:
            return request.not_found()

        postulation_id.ensure_one()
        lang = postulation_id.partner_id.partner_id.lang or 'es_CO'

        # Execute business logic ONLY if in 'notified' state
        if postulation_id.state == 'notified':
            postulation_id.write({'state': 'confirm', 'acceptance_date': datetime.now()})
            postulation_id.message_post(body=_(\
                '%s ACEPTÓ el beneficio desde el correo electrónico.' % str(postulation_id.partner_id.partner_id.name)))

            # adding attachment to partner
            postulation_id.attach_OM_2_partner(postulation_id)

            if postulation_id.product_id.benefit_type == 'colabora':
                postulation_id.calculate_end_date_colabora()

        return request.render('rvc.accept_rvc_benefit_page_view', {
            'benefit_application': postulation_id, 'token': token
        })
