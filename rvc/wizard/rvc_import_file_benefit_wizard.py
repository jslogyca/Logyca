# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import xlwt
import base64
import io
import xlsxwriter
import requests
import tempfile
import xlrd
import logging
import time
import re

class RVCImportFileBenefitWizard(models.TransientModel):
    _name = 'rvc.import.file.benefit.wizard'
    _description = 'RVC Import File Benefit Wizard'

    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    
    def validate_mail(self, email):
        if email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(email.lower()))
        if match == None:
            return False
        return True

    def import_file(self):
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno. \n\n Si no es posible cierre este asistente e intente de nuevo.')

        # valida que el archivo cargado se llame igual que la plantilla .xlsx
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
        #contador de registros en el excel
        count=1
        #contador de postulaciones creadas correctamente en odoo.
        cre=[]
        #almacena las excepciones
        errors=[]
        #almacena las excepciones
        error=[]
        for fila in record_list:
            rvc_beneficiary_id = False
            partner_id = False
            count+=1

            #validar si están los NIT de las empresas (benef y halonadora)
            if fila[0]:
                
                beneficiary_nit = str(fila[0])
                validation = ''

                #tratamiento para los nits que a veces aparecen con .0 al final cuando se cargan
                suffix = ".0"
                if beneficiary_nit.endswith(suffix):
                    beneficiary_nit = beneficiary_nit[:-len(suffix)]
                partner_id = self.env['res.partner'].search([('vat','=',str(beneficiary_nit)), ('parent_id','=',None)])
                if partner_id:
                    try:
                        with self._cr.savepoint():
                            rvc_beneficiary_id = self.env['rvc.beneficiary'].create({
                                                                'partner_id': partner_id.id,
                                                                'vat': partner_id.vat,
                                                                # 'contact_name': str(fila[5]),
                                                                # 'contact_phone': str(fila[7]),
                                                                # 'contact_email': str(fila[6]).strip().lower(),
                                                                # 'contact_position': str(fila[8]),
                                                                'active': True})
                    except Exception as e:
                        validation = "Fila %s: %s no se pudo crear como empresa beneficiaria. %s" % (str(count), partner_id.vat + '-' + str(partner_id.name.strip()),str(e))
                        errors.append(validation)
                        continue
                    cre.append(rvc_beneficiary_id.id)
                    self.env.cr.commit()

        if len(errors)>=1:
            error.append(errors)
        if error:
            msj='El resultado de la importación es: \n\n'
            for e in errors:
                msj+=str(e)
                msj+='\n\n'

            raise ValidationError(msj)            
        obj_model = self.env['ir.model.data']
        res = obj_model.get_object_reference('rvc', 'view_rvc_beneficiary_kanban')

        if not cre:
            raise UserError(_("No se importaron postulaciones a beneficios RVC."))
        return {
            'name': 'Registros Importados '+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'rvc.beneficiary',
            'views': [([res and res[1] or False], 'kanban')],
            'domain': [('id','in',cre)],
            'target': 'current'
        }
