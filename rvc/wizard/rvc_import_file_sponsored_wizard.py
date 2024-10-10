# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
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


class RVCImportFileSponsoredWizard(models.TransientModel):
    _name = 'rvc.import.file.sponsored.wizard'
    _description = 'RVCImport File Sponsored Wizard'

    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')


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
        record_list = record_list[1:]
        count=1
        cre=[]
        for fila in record_list:
            if count<8:
                count+=1
                continue
            if fila[0] and fila[1]:
                # Validar con el nit de la empresa Patrocinadora que esté registrado en Odoo
                partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                if not partner_id:
                    # raise ValidationError('La empresa beneficiaria no existe en Odoo')
                    validation = 'La empresa beneficiaria no existe en Odoo' + ' - ' + str(fila[0])
                    self.env['log.import.rvc'].create({
                                                        'name': validation,
                                                        'date_init': fields.Datetime.now(),
                                                        'user_id' : self.env.user.id})
                    continue
                # Validar que la empresa Patrocinadora esté activa
                if not partner_id.active:
                    # raise ValidationError('La empresa beneficiaria no esta activa')
                    validation = 'La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                    self.env['log.import.rvc'].create({
                                                        'name': validation,
                                                        'date_init': fields.Datetime.now(),
                                                        'user_id' : self.env.user.id})
                    continue
                # Validar que el tipo de vinculación de la empresa Patrocinadora sea miembro
                if partner_id.x_type_vinculation and partner_id.x_type_vinculation.code not in ('01'):
                    # raise ValidationError('El tipo de vinculación de la empresa Patrocinadora no es miembro')
                    validation = 'El tipo de vinculación de la empresa Patrocinadora no es miembro' + ' - ' + str(fila[0])
                    self.env['log.import.rvc'].create({
                                                        'name': validation,
                                                        'date_init': fields.Datetime.now(),
                                                        'user_id' : self.env.user.id})
                    continue
                rvc_patroc = self.env['rvc.sponsor'].create({
                                                    'name': partner_id.name + ' - ' + 'RVC',
                                                    'partner_id': partner_id.id,
                                                    'state': 'confirm',
                                                    'contact_name': str(fila[3])})
                cre.append(rvc_patroc.id)
                self.env.cr.commit()
        obj_model = self.env['ir.model.data']
        res = obj_model.get_object_reference('rvc', 'rvc_sponsor_tree')
        return {
            'name': 'Registros Importados'+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'rvc.sponsor',
            'views': [([res and res[1] or False], 'tree')],
            'domain': [('id','in',cre)],
            'target': 'current'
        }                    