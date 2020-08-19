# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime

try: 
    import qrcode
except ImportError:
    qrcode = None

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
    
class SurveyQuestion(models.Model):
    _inherit = 'survey.question'
    
    question_type = fields.Selection(selection_add = [('little_faces', 'Califíquenos')], string='Question Type')
    
    
class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'
    
    answer_type = fields.Selection(selection_add = [('little_faces', 'little_faces')], string='Answer Type')
    value_little_faces = fields.Integer('Nivel de Satisfacción (Emojis)')
    
    @api.constrains('answer_type')
    def _check_answer_type(self):
        for uil in self:
            fields_type = {
                'text': bool(uil.value_text),
                'number': (bool(uil.value_number) or uil.value_number == 0),
                'date': bool(uil.value_date),
                'free_text': bool(uil.value_free_text),
                'suggestion': bool(uil.value_suggested),
                'little_faces': bool(uil.value_little_faces)
            }
            if not fields_type.get(uil.answer_type, True):
                raise ValidationError(_('The answer must be in the right type'))
    
    @api.model
    def save_line_little_faces(self, user_input_id, question, post, answer_tag):
        vals = {
            'user_input_id': user_input_id,
            'question_id': question.id,
            'survey_id': question.survey_id.id,
            'skipped': False
        }
        if answer_tag in post and post[answer_tag].strip():
            vals.update({'answer_type': 'little_faces', 'value_little_faces': post[answer_tag]})
        else:
            vals.update({'answer_type': None, 'skipped': True})
        old_uil = self.search([
            ('user_input_id', '=', user_input_id),
            ('survey_id', '=', question.survey_id.id),
            ('question_id', '=', question.id)
        ])
        if old_uil:
            old_uil.write(vals)
        else:
            old_uil.create(vals)
        return True