# -*- coding: utf-8 -*-

from odoo import models, http
from odoo.http import request
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
import base64
from odoo.exceptions import Warning

# class Binary(http.Controller):

#     def document(self, filename, filecontent):
#         if not filecontent:
#             return request.not_found()
#         else:

#             headers=[('Content-Type', 'application/vnd.ms-excel'), ('Content-Disposition', content_disposition(filename))
#             ]
#             return request.make_response(filecontent, headers=headers, cookies=None)

#     @http.route(["/download/xlsx/envio/<model('report.excel.sale.product.wizard'):document_id>"], type='http', auth='user')
#     @serialize_exception
#     def download_document(self, document_id, **post):
#         filename = ('%s.xlsx' % document_id.data_name).replace(' ', '_')
#         filecontent = document_id.data
#         return self.document(filename, filecontent)


    # @http.route(["/download/xlsx/envio/<model('report.excel.sale.product.wizard'):document_id>"], type='http', auth='user')
    # @serialize_exception
    # def download_document_zip(self, document_id, **post):
    #     filename = document_id.data_name
    #     filecontent = document_id.data
    #     return self.document(filename, filecontent)    

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