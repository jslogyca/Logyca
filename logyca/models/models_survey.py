# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import random
import pytz


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
        
        #Traer Preguntas 
        obj_survey_question = self.env['survey.question'].search([('survey_id', '=', self.id),('is_page','=',False)])
        #Traer entrada de usuario
        obj_survey_user_input = self.env['survey.user_input'].search([('survey_id', '=', self.id)])
        #Traer label
        question_matrix = []
        for question in obj_survey_question: 
            matrix = []
            obj_survey_label = self.env['survey.label'].search([('question_id_2', '=', question.id)])

            if obj_survey_label:
                matrix.append(question.title)
                for label in obj_survey_label:
                    matrix.append(label.value)
                question_matrix.append(matrix)
                
        #query_columns = '''
        #    Select distinct
        #            b.title || ' ' || case when d.value_suggested_row is not null then e.value else '' end  as Pregunta
        #            from survey_survey as A
        #            inner join survey_question as b on b.survey_id  = a.id
        #            inner join survey_user_input as c on c.survey_id = a.id
        #            inner join survey_user_input_line as d on D.user_input_id = c.id and a.id = d.survey_id and b.id = d.question_id
        #            left join survey_label as e on d.value_suggested  = e.id
        #            left join survey_label as f on d.value_suggested_row  = f.id
        #            where a.id = %s
        #''' % (self.id)
        
        #self._cr.execute(query_columns)
        #result_columns = self._cr.dictfetchall()
        
        columns_str = ''
        for question in obj_survey_question: 
            text_question = question.title
            
            #Recorrer Array question matrix
            text_questions_matrix = ''
            for m in question_matrix:
                text_question_q = ''
                i = 1
                for q in m:         
                    if i == 1:
                        text_question_q = q
                    if text_question_q == text_question and i != 1:  
                        if text_questions_matrix != '':
                            text_questions_matrix = text_questions_matrix+'|'+text_question_q+' - '+q                            
                        else:
                            text_questions_matrix = text_question_q+' - '+q                                            
                    i = i + 1
                if text_questions_matrix:
                    text_question = text_questions_matrix
                
            #Asignar Columnas
            if columns_str != '':
                columns_str = columns_str+'|'+text_question
            else:
                columns_str = text_question
        
        #columns_str = 'Encuesta creada por|Quien Responde|'+columns_str
        columns = columns_str.split("|")
        #raise ValidationError(_(columns))    
        
        #Traer Consultas
        
        #Traer Preguntas 
        obj_survey_question = self.env['survey.question'].search([('survey_id', '=', self.id),('is_page','=',False)])

        #Traer entrada de usuario
        obj_survey_user_input = self.env['survey.user_input'].search([('survey_id', '=', self.id),('state','=','done')])

        format = "%d-%m-%Y %H:%M:%S"

        # Tiempo actual en UTC
        local_tz = pytz.timezone('US/Central')

        results = []
        for user_input in obj_survey_user_input:
            result_user = []
            result_user.append('IDUSER:'+str(user_input.id))
            result_user.append('Fecha de Diligenciamiento')
            date_tz = user_input.create_date.astimezone(local_tz).strftime(format)
            result_user.append(str(date_tz))

            for question in obj_survey_question:
                obj_survey_user_input_line = self.env['survey.user_input.line'].search([('survey_id', '=', self.id),('user_input_id','=',user_input.id),('question_id','=',question.id)])
                for result in obj_survey_user_input_line:
                    if result.value_suggested and result.value_suggested_row: 
                        result_user.append(question.title+' - '+result.value_suggested_row.value)
                    else:
                        result_user.append(question.title)

                    if result.value_text:
                        result_user.append(result.value_text)
                    if result.value_number:
                        result_user.append(result.value_number)
                    if result.value_date:
                        result_user.append(result.value_date)
                    if result.value_datetime:
                        result_user.append(result.value_datetime)
                    if result.value_free_text:
                        result_user.append(result.value_free_text)
                    if result.value_little_faces:
                        result_user.append(result.value_little_faces)
                    if result.value_suggested:
                        result_user.append(result.value_suggested.value)                    
                    #value_suggested,value_suggested_row
            results.append(result_user)
        
        if results and columns:             
            filename= 'Resultados-'+str(self.title)+'.xlsx'
            stream = io.BytesIO()
            book = xlsxwriter.Workbook(stream, {'in_memory': True})
            sheet = book.add_worksheet(str(self.title))

            #Agregar columnas
            aument_columns = 0

            #Agregar nombre de primera columna
            sheet.write(0, aument_columns, "Fecha de Diligenciamiento")

            aument_columns = aument_columns + 1
            for col in columns:            
                sheet.write(0, aument_columns, col)
                aument_columns = aument_columns + 1
                
            #Agregar respuestas
            i_user = 1
            aument_columns = 0
            aument_rows = 1
            id_user = ''
            id_user_ant = ''
            str_pregunta = ''
            str_respuesta = ''
            for query in results:                
                if i_user == 1:
                    id_user_ant = query[0]                    
                else:
                    id_user_ant = id_user 
                id_user = query[0]
                
                if id_user != id_user_ant:                      
                    aument_rows = aument_rows + 1
                
                i = 1
                for result_x_user in query:
                    if i != 1:
                        #Si la posición en el array es par es pregunta sino es respuesta
                        if i % 2 == 0:
                            str_pregunta = result_x_user
                        else:
                            str_respuesta = result_x_user
                        
                        if str_pregunta and str_respuesta:
                            position_col = 0
                            for col in columns:
                                if col == str_pregunta:                                    
                                    sheet.write(aument_rows, position_col, str_respuesta)
                                    str_pregunta = ''
                                    str_respuesta = ''
                                position_col = position_col + 1                    
                    i = i + 1
                    
                    
                i_user = i_user + 1
            
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
    _inherit = 'survey.user_input.line'
    
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