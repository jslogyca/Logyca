# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
from odoo.tools.misc import get_lang


class AcceptRvcBenefit(http.Controller):

    @http.route('/rvc/accept_benefit/<string:token>', type='http', auth="public", website=True)
    def accept_benefit(self, token, **kwargs):
        postulation_id = request.env['benefits.admon'].sudo().search([('access_token', '=', token)])
        if not postulation_id:
            return request.not_found()

        # Marcar la posituación como aceptada
        if postulation_id.state == 'notified':
            postulation_id.write({'state': 'confirm'})
            postulation_id.message_post(body=_('%s <u><strong>ACEPTÓ</strong></u> el beneficio desde el correo electrónico.' % str(postulation_id.partner_id_partner_id.name)))

        lang = postulation_id.partner_id.partner_id.lang
        return request.env['ir.ui.view'].with_context(lang=lang).render_template('rvc.accept_rvc_benefit_page_view', {
            'benefits_admon': postulation_id, 'token': token
        })