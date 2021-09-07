# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import base64

class Binary(http.Controller):

    @http.route('/web/binary/download_document', type='http', auth="public")
    @serialize_exception
    def download_document(self, model, id, filename=None, **kw):
        """ Download link for files stored as binary fields.
        :param str model: name of the model to fetch the binary from
        :param str field: binary field
        :param str id: id of the record from which to fetch the binary
        :param str filename: field holding the file's name, if any
        :returns: :class:`werkzeug.wrappers.Response`
        """
        record = request.env[model].browse(int(id))
        binary_file = record.data # aqui colocas el nombre del campo binario que almacena tu archivo
        filecontent = base64.b64decode(binary_file or '')
        content_type, disposition_content = False, False

        if not filecontent:
            return request.not_found()
        else:
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
            content_type = ('Content-Type', 'application/octet-stream')
            disposition_content = ('Content-Disposition', content_disposition(filename))

        return request.make_response(filecontent, [content_type,
                                                   disposition_content])