# -*- coding: utf-8 -*-
from io import BytesIO
from zipfile import ZipFile

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

    @http.route(["/download/xml/envio/<model('einvoice.document'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document(self, document_id, **post):
        filename = ('%s' % document_id.name).replace(' ', '_')
        filecontent = document_id.xml_document
        return self.document(filename, filecontent)

    @http.route(["/download/zip/envio/<model('einvoice.document'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document_zip(self, document_id, **post):

        attachment_ids_search = document_id.env['ir.attachment'].search([('res_model','=','account.move'),
                                                                ('res_id','=', document_id.invoice_id.id)])
        
        existe = attachment_ids_search.filtered( lambda x: x.name == document_id.filename)
        if not existe:
            adjuntos_extras = False
            if attachment_ids_search:
                sio1 = BytesIO()
                zf1 = ZipFile(sio1, 'a')
                for x in attachment_ids_search:
                    if not x.name == ('%s.pdf' %document_id.invoice_id.name) or x.name == ('%s' % document_id.name).replace(' ', '_'):
                        zf1.writestr(x.name, base64.b64decode(x.datas))
                        adjuntos_extras = True
                zf1.close()
                sio1.seek(0)
                file_zip1 = sio1.getvalue()
            
            report = document_id.env['ir.actions.report']._get_report_from_name('account.report_invoice_with_payments')
            sio = BytesIO()
            zf = ZipFile(sio, 'a')
            name_xml = ('%s' % document_id.name).replace(' ', '_')
            zf.writestr(name_xml, document_id.xml_document.encode('UTF-8'))
            zf.writestr(('%s.pdf' %document_id.invoice_id.name), report._render_qweb_pdf(document_id.invoice_id.ids)[0])
            if adjuntos_extras:
                zf.writestr('extras.zip', file_zip1)
            zf.close()
            sio.seek(0)
            file_zip = sio.getvalue()
        else:
            for x in existe:
                file_zip = base64.b64decode(x.datas)


        filename = document_id.filename
        filecontent = file_zip

        return self.document(filename, filecontent)

    @http.route(["/download/xml/enviods/<model('account.move'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document_ds(self, document_id, **post):
        filename = ('%s' % document_id.ds_name).replace(' ', '_')
        filecontent = document_id.xml_ds_document
        return self.document(filename, filecontent)

    @http.route(["/download/attachment/envio/<model('einvoice.document'):document_id>"], type='http', auth='user')
    @serialize_exception
    def download_document(self, document_id, **post):
        filename = ('%s' % document_id.attachedxml).replace(' ', '_')
        filecontent = document_id.attached_document_xml
        return self.document(filename, filecontent)