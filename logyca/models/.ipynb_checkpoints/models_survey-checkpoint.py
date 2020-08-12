# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import qrcode
import base64
import io

#Encuestas
class Survey(models.Model):
    _inherit = 'survey.survey'
    
    qr_survey = fields.Binary('QR Survey')
    qr_survey_name = fields.Char(default="survey_qr.png")
    
    def generate_qr(self):
        qr = qrcode.QRCode(version=1,error_correction=qrcode.constants.ERROR_CORRECT_L,box_size=20,border=4,)
        name = self.title+'_QR.png'
        qr.add_data(self.public_url)
        qr.make(fit=True)
        img = qr.make_image()
        buffer = io.BytesIO()        
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue())
        self.write({'qr_survey': img_str,'qr_survey_name':name})
        
        action = {
                      'name': 'QrEncuesta',
                      'type': 'ir.actions.act_url',
                      'url': "web/content/?model=survey.survey&id=" + str(self.id) + "&filename_field=qr_survey_name&field=qr_survey&download=true&filename=" + self.qr_survey_name,
                      'target': 'self',
                   }
        return action

    
