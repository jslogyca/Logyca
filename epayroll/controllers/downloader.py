# -*- coding: utf-8 -*-

from odoo import models, http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import base64
from odoo.exceptions import Warning

class Binary(http.Controller):

    def document(self, filename, filecontent):
        if not filecontent:
            return request.not_found()
        else:
            headers = [
             ('Content-Type', 'application/xml'),
             (
              'Content-Disposition', content_disposition(filename)),
             ('charset', 'utf-8')]
            return request.make_response(filecontent, headers=headers, cookies=None)


    @http.route(["/download/xml/epayslip/<model('epayslip.bach'):epayslip_id>"], type='http', auth='user')
    @serialize_exception
    def download_document(self, epayslip_id, **post):
        filename = ('%s' % epayslip_id.name).replace(' ', '_')
        filecontent = epayslip_id.xml_document
        return self.document(filename, filecontent)