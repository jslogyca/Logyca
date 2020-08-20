# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import random

try: 
    import qrcode
except ImportError:
    qrcode = None

import base64
import io
import xlwt
import xlsxwriter
import requests

#Encuestas
class Survey(models.Model):
    _inherit = 'survey.survey'
    
    qr_survey = fields.Binary('QR Survey')
    qr_survey_name = fields.Char(default="survey_qr.png")
    excel_file_result = fields.Binary('Excel file result')
    excel_file_result_name = fields.Char('Excel file result name', size=64)
        
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

    def generate_excel(self):
        #Traer Columnas
        query_columns = '''
            Select distinct
                    b.title || ' ' || case when d.value_suggested_row is not null then e.value else '' end  as Pregunta
                    from survey_survey as A
                    inner join survey_question as b on b.survey_id  = a.id
                    inner join survey_user_input as c on c.survey_id = a.id
                    inner join survey_user_input_line as d on D.user_input_id = c.id and a.id = d.survey_id and b.id = d.question_id
                    left join survey_label as e on d.value_suggested  = e.id
                    left join survey_label as f on d.value_suggested_row  = f.id
                    where a.id = %s
        ''' % (self.id)
        
        self._cr.execute(query_columns)
        result_columns = self._cr.dictfetchall()
        
        columns_str = ''
        for c in result_columns: 
                for row in c.values():
                    if columns_str != '':
                        columns_str = columns_str+','+row
                    else:
                        columns_str = row
        
        columns_str = 'Encuesta creada por,Quien Responde,'+columns_str
        columns = columns_str.split(",")
        #raise ValidationError(_(columns))    
        
        #Traer Consultas
        query = '''
            Select c.id,
                b.title || ' ' || case when d.value_suggested_row is not null then e.value else '' end  as Pregunta,
                Usu_respu.name as Usuario_Respuesta,
                case when d.answer_type = 'text' then d.value_text
                    when d.answer_type = 'number' then cast(d.value_number as varchar)
                    when d.answer_type = 'date' then cast(d.value_date as varchar)
                    when d.answer_type = 'datetime' then cast(d.value_datetime as varchar)
                    when d.answer_type = 'suggestion' and d.value_suggested_row is null then cast(e.value as varchar)
                    when d.answer_type = 'suggestion' and d.value_suggested_row is not null then cast(f.value as varchar)
                    when d.answer_type = 'free_text' then cast(d.value_free_text as varchar) 
                    when d.answer_type = 'little_faces' then cast(d.value_little_faces as varchar) else '' end as Respuesta,
                usu_crea."name" as Encuenta_Creada_Por
                from survey_survey as A
                inner join survey_question as b on b.survey_id  = a.id
                inner join survey_user_input as c on c.survey_id = a.id
                inner join survey_user_input_line as d on D.user_input_id = c.id and a.id = d.survey_id and b.id = d.question_id
                left join survey_label as e on d.value_suggested  = e.id
                left join survey_label as f on d.value_suggested_row  = f.id
                left join res_users n on n.id = a.create_uid
                left join res_users o on o.id = a.write_uid
                left join res_users p on p.id = c.write_uid
                left join res_partner usu_crea on usu_crea.id = n.partner_id
                left join res_partner usu_mod on usu_mod.id = o.partner_id
                left join res_partner Usu_respu on Usu_respu.id = p.partner_id
                where a.id = %s 
                order by c.id, b."sequence"
        ''' % (self.id)
                    
        self._cr.execute(query)
        result_query = self._cr.dictfetchall()
        
        if result_query and columns:             
            filename= 'Resultados-'+str(self.title)+'.xlsx'
            stream = io.BytesIO()
            book = xlsxwriter.Workbook(stream, {'in_memory': True})
            sheet = book.add_worksheet(str(self.title))

            #Agregar columnas
            aument_columns = 0
            for col in columns:            
                sheet.write(0, aument_columns, col)
                aument_columns = aument_columns + 1
                
            #Agregar query
            i = 0
            aument_columns = 0
            aument_rows = 1
            id_user = 0
            id_user_ant = 0
            str_pregunta = ''
            str_respuesta = ''
            str_quien_responde = ''
            str_encuesta_creada_por = ''
            for query in result_query:                 
                if i == 0:
                    id_user_ant = query['id']
                else:
                    id_user_ant = id_user                
                id_user = query['id']
                
                str_encuesta_creada_por = query['encuenta_creada_por']
                str_quien_responde = query['usuario_respuesta']
                
                if id_user != id_user_ant:                      
                    aument_rows = aument_rows + 1
                
                sheet.write(aument_rows, 0, str_encuesta_creada_por)
                sheet.write(aument_rows, 1, str_quien_responde)
                
                for row in query.values():
                    if aument_columns == 1:
                        str_pregunta = row 
                    if aument_columns == 3:
                        str_respuesta = row                     
                    position_col = 0
                    for col in columns:
                        if col == str_pregunta:
                            sheet.write(aument_rows, position_col, str_respuesta)
                        position_col = position_col + 1                    
                    aument_columns = aument_columns + 1
                
                aument_columns = 0
                i = i + 1
            
            book.close()
            
            self.write({
                'excel_file_result': base64.encodestring(stream.getvalue()),
                'excel_file_result_name': filename,
            })
            
            action = {
                        'name': str(self.title),
                        'type': 'ir.actions.act_url',
                        'url': "web/content/?model=survey.survey&id=" + str(self.id) + "&filename_field=excel_file_result_name&field=excel_file_result&download=true&filename=" + self.excel_file_result_name,
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