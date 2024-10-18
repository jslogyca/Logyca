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


class BenefImportFileMemberWizard(models.TransientModel):
    _name = 'benefi.import.file.member.wizard'
    _description = 'Benef Import File Member Wizard'

    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)    
    
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
                
                beneficiary_nit = str(fila[1])
                validation = ''

                #tratamiento para los nits que a veces aparecen con .0 al final cuando se cargan
                suffix = ".0"
                if beneficiary_nit.endswith(suffix):
                    beneficiary_nit = beneficiary_nit[:-len(suffix)]
                partner_id = self.env['res.partner'].search([('vat','=',str(beneficiary_nit)), ('parent_id','=',None)])
                if partner_id:
                    if fila[3]:
                        bene_name = str(fila[3])
                        company_user_id = str(fila[4])
                        company_email = str(fila[5])
                        formato = '%Y-%m-%dT%H:%M:%S'
                        date_done = fila[0]
                        benef_id = self.env['benefits.membership'].search([('name','=',str(bene_name)), ('active','=',True)])
                        if benef_id:
                            exis_benef = self.env['benefits.membership.partner'].search([('partner_id','=',partner_id.id), 
                                                                    ('benefit_id','=',benef_id.id),
                                                                    ('date_done','=',date_done)])
                            if exis_benef:
                                continue                            
                            try:
                                with self._cr.savepoint():
                                    benef_ids = self.env['benefits.membership.partner'].create({
                                                                        'partner_id': partner_id.id,
                                                                        'vat': partner_id.vat,
                                                                        'company_id': self.company_id.id,
                                                                        'benefit_id': benef_id.id,
                                                                        'categ_id': benef_id.categ_id.id,
                                                                        'company_user': company_user_id or '',
                                                                        'company_email': company_email or '',
                                                                        'date_done': date_done})
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
        # obj_model = self.env['ir.model.data']
        # res = obj_model.get_object_reference('crm_allies', 'benefits_membership_partner_view_tree')
        view_id = self.env.ref('crm_allies.benefits_membership_partner_view_tree').id,

        if not cre:
            raise UserError(_("No se importaron los beneficios"))
        return {
            'name': 'Registros Importados '+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'benefits.membership.partner',
            'views': [(view_id, 'tree')],
            'view_id': view_id,
            'domain': [('id','in',cre)],
            'target': 'current'
        }
