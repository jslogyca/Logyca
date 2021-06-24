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

class RVCImportFileWizard(models.TransientModel):
    _name = 'rvc.import.file.wizard'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    type_beneficio = fields.Selection([('codigos', 'Identificación de Productos'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], string="Beneficio")                                  
        

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
                if self.type_beneficio == 'codigos':
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                    if not partner_id:
                        # raise ValidationError('La empresa beneficiaria no exise en Odoo')
                        validation = 'La empresa beneficiaria no exise en Odoo' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        # raise ValidationError('La empresa beneficiaria no esta activa')
                        validation = 'La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Date.today(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPYME)
                    if partner_id.x_company_size not in ('6', '5', '3'):
                        # raise ValidationError('el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)')
                        validation = 'el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                        
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    benf_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id),('type_beneficio','=',self.type_beneficio)])
                    if benf_id:
                        # raise ValidationError('La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio)')
                        validation = 'La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                         
                    # Validar que el tipo de vinculación de la empresa beneficiaria no sea miembro, ni cliente CE
                    if partner_id.x_type_vinculation and partner_id.x_type_vinculation.code in ('01', '02'):
                        # raise ValidationError('El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE')
                        validation = 'El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                         
                    product_id=self.env['config.rvc'].search([('type_beneficio','=',self.type_beneficio)])
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsored'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Patrocinadora no existe' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                         
                    rvc_benf = self.env['rvc.beneficiary'].create({
                                                        'name': partner_id.name + '-' + 'Identificación de Productos',
                                                        'partner_id': partner_id.id,
                                                        'name_contact': str(fila[4]),
                                                        'cant_cod': str(fila[2]),
                                                        'parent_id' : sponsored_id.partner_id.id,
                                                        'state': 'confirm',
                                                        'type_beneficio' : self.type_beneficio})
                    cre.append(rvc_benf.id)
                    self.env.cr.commit()
                elif self.type_beneficio == 'colabora':
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                    if not partner_id:
                        # raise ValidationError('La empresa beneficiaria no exise en Odoo')
                        validation = 'La empresa beneficiaria no exise en Odoo' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        # raise ValidationError('La empresa beneficiaria no esta activa')
                        validation = 'La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Date.today(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPYME)
                    if partner_id.x_company_size not in ('6', '5'):
                        # raise ValidationError('el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)')
                        validation = 'el tamaño de la empresa beneficiaria no es micro Oo pequeña (MIPY)' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                        
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    benf_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id),('type_beneficio','=',self.type_beneficio)])
                    if benf_id:
                        # raise ValidationError('La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio)')
                        validation = 'La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el Patrocinador exista
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsored'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Patrocinadora no existe' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el patrocinador no tenga otra postulación o entrega activa de este beneficio para otra empresa beneficiaria
                    benf_patro_id=self.env['rvc.beneficiary'].search([('parent_id','=',parent_id.id),('type_beneficio','=',self.type_beneficio)])
                    if not benf_patro_id:
                        validation = 'El patrocinador tiene otra postulación o entrega activa de este beneficio para otra empresa beneficiaria' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue 

                    rvc_benf = self.env['rvc.beneficiary'].create({
                                                        'name': partner_id.name + '-' + 'Identificación de Productos',
                                                        'partner_id': partner_id.id,
                                                        'name_contact': str(fila[4]),
                                                        'cant_cod': str(fila[2]),
                                                        'parent_id' : sponsored_id.partner_id.id,
                                                        'state': 'confirm',
                                                        'type_beneficio' : self.type_beneficio})
                    cre.append(rvc_benf.id)
                    self.env.cr.commit()
                else:
                    print('VALIDACIONES ANALITICA')
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                    if not partner_id:
                        # raise ValidationError('La empresa beneficiaria no exise en Odoo')
                        validation = 'La empresa beneficiaria no exise en Odoo' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        # raise ValidationError('La empresa beneficiaria no esta activa')
                        validation = 'La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Date.today(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPYME)
                    if partner_id.x_company_size not in ('6', '5'):
                        # raise ValidationError('el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)')
                        validation = 'el tamaño de la empresa beneficiaria no es micro Oo pequeña (MIPY)' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                        
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    benf_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id),('type_beneficio','=',self.type_beneficio)])
                    if benf_id:
                        # raise ValidationError('La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio)')
                        validation = 'La empresa beneficiaria tiene otra postulación o entrega activa de este beneficio' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el Patrocinador exista
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsored'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Patrocinadora no existe' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el patrocinador no tenga otra postulación o entrega activa de este beneficio para otra empresa beneficiaria
                    benf_patro_id=self.env['rvc.beneficiary'].search([('parent_id','=',parent_id.id),('type_beneficio','=',self.type_beneficio)])
                    if not benf_patro_id:
                        validation = 'El patrocinador tiene otra postulación o entrega activa de este beneficio para otra empresa beneficiaria' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue 

                    rvc_benf = self.env['rvc.beneficiary'].create({
                                                        'name': partner_id.name + '-' + 'Identificación de Productos',
                                                        'partner_id': partner_id.id,
                                                        'name_contact': str(fila[4]),
                                                        'cant_cod': str(fila[2]),
                                                        'parent_id' : sponsored_id.partner_id.id,
                                                        'state': 'confirm',
                                                        'type_beneficio' : self.type_beneficio})
                    cre.append(rvc_benf.id)
                    self.env.cr.commit()                    

        obj_model = self.env['ir.model.data']
        res = obj_model.get_object_reference('rvc', 'rvc_beneficiary_tree')
        return {
            'name': 'Registros Importados'+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'rvc.beneficiary',
            'views': [([res and res[1] or False], 'tree')],
            'domain': [('id','in',cre)],
            'target': 'current'
        }
                    