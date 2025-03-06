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

import pytz


class CRMLeadImportFileWizard(models.TransientModel):
    _name = 'crm.lead.import.file.wizard'
    _description = 'CRM Lead Import File Wizard'

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
            if fila[1]:
                
                beneficiary_nit = str(fila[0])
                company_name = str(fila[3])
                validation = ''
                expected_revenue = 0.0

                #tratamiento para los nits que a veces aparecen con .0 al final cuando se cargan
                suffix = ".0"
                if beneficiary_nit.endswith(suffix):
                    beneficiary_nit = beneficiary_nit[:-len(suffix)]
                partner_id = self.env['res.partner'].search([('vat','=',str(beneficiary_nit)), ('parent_id','=',None)], limit=1)
                company_id = self.env['res.company'].search([('name','=',str(company_name))], limit=1)
                expected_revenue = fila[4]
                bene_name = str(fila[2])
                user_id = 263
                source_id = 140
                description = str(fila[7])
                partner_name = str(fila[1])
                contact_name = str(fila[8])
                street = str(fila[9])
                mobile = str(fila[10])
                email_from = str(fila[11])
                print('EMPRESA', partner_id)
                if partner_id:
                    formato = '%Y-%m-%dT%H:%M:%S'
                    print('EMPRESA2222', partner_id.id, bene_name, company_id)
                    try:
                        with self._cr.savepoint():
                            benef_ids = self.env['crm.lead'].create({
                                                'partner_id': partner_id.id,
                                                'name': bene_name,
                                                'expected_revenue': expected_revenue,
                                                'type': 'opportunity',
                                                'user_id': user_id,
                                                'source_id': source_id,
                                                'description': description,
                                                'contact_name': contact_name,
                                                'street': street,
                                                'mobile': mobile,
                                                'email_from': email_from,
                                                'phone': mobile,
                                                'company_id': company_id.id})
                        print('EMPRESA3333', benef_ids)
                    except Exception as e:
                        validation = "Fila %s: %s no se pudo crear como empresa beneficiaria. %s" % (str(count), partner_id.vat + '-' + str(partner_id.name.strip()),str(e))
                        errors.append(validation)
                        continue
                    cre.append(benef_ids.id)
                    self.env.cr.commit()
                else:
                    try:
                        with self._cr.savepoint():
                            benef_ids = self.env['crm.lead'].create({
                                                'partner_name': partner_name,
                                                'contact_name': contact_name,
                                                'mobile': mobile,
                                                'phone': mobile,
                                                'email_from': email_from,
                                                'street': street,
                                                'name': bene_name,
                                                'expected_revenue': expected_revenue,
                                                'type': 'opportunity',
                                                'user_id': user_id,
                                                'source_id': source_id,
                                                'description': description,
                                                'company_id': company_id.id})
                        print('EMPRESA3333', benef_ids)
                    except Exception as e:
                        validation = "Fila %s: %s no se pudo crear como empresa beneficiaria. %s" % (str(count), partner_id.vat + '-' + str(partner_id.name.strip()),str(e))
                        errors.append(validation)
                        continue
                    cre.append(benef_ids.id)
                    self.env.cr.commit()

        if len(errors)>=1:
            error.append(errors)
        if error:
            msj='El resultado de la importación es: \n\n'
            for e in errors:
                msj+=str(e)
                msj+='\n\n'

            raise ValidationError(msj)
        view_id = self.env.ref('crm.crm_case_tree_view_oppor').id,

        if not cre:
            raise UserError(_("No se importaron los beneficios"))
        return {
            'name': 'Registros Importados '+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm.lead',
            'views': [(view_id, 'tree')],
            'view_id': view_id,
            'domain': [('id','in',cre)],
            'target': 'current'
        }
