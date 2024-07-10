    # -*- coding: utf-8 -*-
from os import write
from odoo import api, fields, models, _
from itertools import product
from odoo.exceptions import ValidationError
import xlwt
import base64
import io
import xlsxwriter
import requests
import tempfile
import xlrd

import time
from datetime import datetime, timedelta
import logging

class ResPartnerUpdateImport(models.TransientModel):
    _name = 'res.partner.update.import'
    _description = 'Partner Update Import'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    
    def col_position_from_key(self, sheet, key):
        for row_index, col_index in product(range(sheet.nrows), range(sheet.ncols)):
            if sheet.cell(row_index, col_index).value == key:
                return col_index

    def import_file(self):   
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno. \n\n Si no es posible cierre este asistente e intente de nuevo.')
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete = False)
            tmp_file.write(base64.b64decode(self and self.file_data or _('Invalid file')))
            tmp_file.close()
            xls_tmp_file = xlrd.open_workbook(tmp_file.name)
        except:
            raise ValidationError('No se puede leer el archivo. Verifique que el formato sea el correcto.')
            return False
        
        sheet = xls_tmp_file.sheet_by_name(xls_tmp_file.sheet_names()[0])
        record_list = [sheet.row_values(i) for i in range(sheet.nrows)]
        partner_identification_loc = self.col_position_from_key(sheet, 'NUMERO DE DOCUMENTO')
        partner_name_loc = int(self.col_position_from_key(sheet, 'NOMBRE DEL CONTACTO'))
        email_contact_loc = int(self.col_position_from_key(sheet, 'CORREO ELECTRONICO'))
        note_contact_loc = int(self.col_position_from_key(sheet, 'NOTA'))
        
        record_list = record_list[1:]
        error = False
        mens_error = 'Observaciones: '
        for fila in record_list:
            partner =self.env['res.partner'].search([('vat','=',str(int(fila[partner_identification_loc]))), ('parent_id','=',None)])
            if not partner:
                error = True
                mens_error = mens_error + 'Empresa con NIT ' + str(int(fila[partner_identification_loc])) + ' no encontrado'
            else:
                contact = self.env['res.partner'].search([('name','=', str(fila[partner_name_loc])), ('parent_id','=',partner.id)])
                if not contact:
                    contact = self.env['res.partner'].search([('email','=', str(fila[email_contact_loc])), ('parent_id','=',partner.id)])
                    if not contact:
                        error = True
                        mens_error = mens_error + 'Contacto ' + str(fila[partner_name_loc]) + ' no encontrado'
                        continue
                contact.write({'active': False, 'x_active_for_logyca': False, 'comment': str(fila[note_contact_loc])})
                # contact.write({'active': False, 'comment': str(fila[note_contact_loc])})
                self.env.cr.commit()
        if error:
            raise ValidationError('¡Error!. "%s"' %  mens_error)
        return True
