# -*- coding: utf-8 -*-

try:
    from BytesIO import BytesIO
except ImportError:
    from io import BytesIO
import zipfile
from datetime import datetime
from odoo import http
from odoo.http import request
from odoo.http import content_disposition
import ast


class Binary(http.Controller):

    @http.route('/web/binary/download_zip', type='http', auth="public")
    def download_document(self,  model, id, reports, filename, **kw):
        report_ids = ast.literal_eval(reports)
        attachment_ids = request.env['ir.attachment'].search([('id', 'in', report_ids)])
        file_dict = {}
        for attachment_id in attachment_ids:
            file_store = attachment_id.store_fname
            if file_store:
                file_name = attachment_id.name
                file_path = attachment_id._full_path(file_store)
                file_dict["%s:%s" % (file_store, file_name)] = dict(path=file_path, name=file_name)

        zip_filename = "%s.zip" % filename
        bit_io = BytesIO()
        zip_file = zipfile.ZipFile(bit_io, "w", zipfile.ZIP_DEFLATED)
        for file_info in file_dict.values():
            zip_file.write(file_info["path"], file_info["name"])
        zip_file.close()
        return request.make_response(bit_io.getvalue(),
                                     headers=[('Content-Type', 'application/x-zip-compressed'),
                                              ('Content-Disposition', content_disposition(zip_filename))])
