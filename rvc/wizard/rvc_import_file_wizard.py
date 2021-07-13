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
    _description = 'Cargue Masivo Derechos de Identificación'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    type_beneficio = fields.Selection([('codigos', 'Derechos de Identificación'), 
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
        e=[]
        error=[]
        for fila in record_list:
            if count<8:
                count+=1
                continue
            if fila[0] and fila[1]:
                if self.type_beneficio == 'codigos':
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                    if not partner_id:
                        validation = 'Por favor corrija el archivo, La empresa beneficiaria no exise en Odoo' + ' - ' + str(fila[0])
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        # raise ValidationError('La empresa beneficiaria no esta activa')
                        validation = 'Por favor corrija el archivo, La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPYME)
                    if partner_id.x_company_size not in ('6', '5', '3'):
                        # raise ValidationError('el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)')
                        validation = 'Por favor corrija el archivo, el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPYME)' + ' - ' + str(fila[0])
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    # Validar que el tipo de vinculación de la empresa beneficiaria no sea miembro, ni cliente CE
                    if partner_id.x_type_vinculation and partner_id.x_type_vinculation.code in ('01', '02'):
                        # raise ValidationError('El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE')
                        validation = 'Por favor corrija el archivo, El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE' + ' - ' + str(fila[0])                      
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    product_id=self.env['product.rvc'].search([('type_beneficio','=',self.type_beneficio)])
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsored'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Halonadora no existe' + ' - ' + str(fila[1])
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    rvc_beneficiary_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id)])
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    if rvc_beneficiary_id:
                        product_benef_id=self.env['product.benef'].search([('partner_id','=',rvc_beneficiary_id.id),('product_id','=',product_id.id)])
                        if product_benef_id:
                            validation = 'La empresa Beneficiaria ya tiene una entrega de beneficio activa' + ' - ' + str(fila[0] + ' - ' + partner_id.name)
                            e.append(validation)
                            continue
                            # raise ValidationError(validation)
                    #CONVENIO
                    agreement_rvc_id = self.env['agreement.rvc'].search([('name','=',str(fila[8])),('active','=',True)])
                    if not agreement_rvc_id:
                        validation = 'El convenio no existe o no esta activo' + ' - ' + str(fila[8])
                        e.append(validation)
                        continue
                        # raise ValidationError(validation)
                    if not rvc_beneficiary_id:
                        # contact_id=self.env['res.partner'].search([('name','=',str(fila[4])), ('is_company','=',False), ('parent_id','=',partner_id.id)], limit=1)
                        # if not contact_id:
                        #     validation = 'El contacto no existe' + ' - ' + str(fila[4])
                        #     e.append(validation)
                        #     continue
                        #     # raise ValidationError(validation)
                        # print('ERRORES556565656565656565656656565')
                        try:
                            print('ERRORES 32323232323')
                            rvc_beneficiary_id = self.env['rvc.beneficiary'].create({
                                                                'name': partner_id.name + '-' + 'Derechos de Identificación',
                                                                'partner_id': partner_id.id,
                                                                'vat': partner_id.vat,
                                                                'name_contact': str(fila[4]),
                                                                'phone_contact': str(fila[6]),
                                                                'email_contact': str(fila[7]),
                                                                'cargo_contact': str(fila[5]),
                                                                'active': True})
                            self.env.cr.commit()
                        except:
                            print('ERRORES 3298989898989', rvc_beneficiary_id)
                            validation = 'La Empresa beneficiaria no se puede crear'
                            e.append(validation)
                            continue
                    print('ERRORES 47474747474747')
                    if rvc_beneficiary_id and rvc_beneficiary_id.id:
                        print('ERRORES 47474747474747', rvc_beneficiary_id, rvc_beneficiary_id.id, str(fila[2]))
                        product_benef = self.env['product.benef'].create({
                                                            'name': partner_id.name + '-' + 'Derechos de Identificación',
                                                            'partner_id': rvc_beneficiary_id.id,
                                                            'parent_id': sponsored_id.id,
                                                            'agreement_id': agreement_rvc_id.id,
                                                            'product_id': product_id.id,
                                                            'cant_cod': str(fila[2])})
                        cre.append(product_benef.id)
                elif self.type_beneficio == 'colabora':
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])
                    if not partner_id:
                        validation = 'Por favor corrija el archivo, La empresa beneficiaria no exise en Odoo' + ' - ' + str(fila[0])
                        raise ValidationError(validation)
                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        # raise ValidationError('La empresa beneficiaria no esta activa')
                        validation = 'Por favor corrija el archivo, La empresa beneficiaria no esta activa' + ' - ' + str(fila[0])
                        raise ValidationError(validation)
                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPY)
                    if partner_id.x_company_size not in ('6', '5'):
                        # raise ValidationError('el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPY)')
                        validation = 'Por favor corrija el archivo, el tamaño de la empresa beneficiaria no es micro, pequeña o mediana (MIPY)' + ' - ' + str(fila[0])                      
                        raise ValidationError(validation)
                    # Validar que el tipo de vinculación de la empresa beneficiaria no sea miembro, ni cliente CE
                    if partner_id.x_type_vinculation and partner_id.x_type_vinculation.code in ('01', '02'):
                        # raise ValidationError('El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE')
                        validation = 'Por favor corrija el archivo, El tipo de vinculación de la empresa beneficiaria es miembro o cliente CE' + ' - ' + str(fila[0])                      
                        raise ValidationError(validation)
                    product_id=self.env['product.rvc'].search([('type_beneficio','=',self.type_beneficio)])
                    self._cr.execute(''' SELECT id FROM sub_product_rvc WHERE product_id=%s AND %s between cant_min AND cant_max and state=%s''', (product_id.id, int(fila[2]), 'activo'))
                    sub_product_id = self._cr.fetchone()
                    if not sub_product_id:
                        validation = 'No existe un subnivel COLABORA configurado para ' + ' - ' + str(fila[2])
                        raise ValidationError(validation)                        
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsored'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Halonadora no existe' + ' - ' + str(fila[1])
                        raise ValidationError(validation)
                    rvc_beneficiary_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id)])
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    if rvc_beneficiary_id:
                        product_benef_id=self.env['product.benef'].search([('partner_id','=',rvc_beneficiary_id.id),('product_id','=',product_id.id)])
                        if product_benef_id:
                            validation = 'La empresa Beneficiaria ya tiene una entrega de beneficio activa' + ' - ' + str(fila[0] + ' - ' + partner_id.name)
                            raise ValidationError(validation)
                    #CONVENIO
                    agreement_rvc_id = self.env['agreement.rvc'].search([('name','=',str(fila[8])),('active','=',True)])
                    if not agreement_rvc_id:
                        validation = 'El convenio no existe o no esta activo' + ' - ' + str(fila[8])
                        raise ValidationError(validation)
                    if not rvc_beneficiary_id:
                        contact_id=self.env['res.partner'].search([('name','=',str(fila[4])), ('is_company','=',False), ('parent_id','=',partner_id.id)], limit=1)
                        if not contact_id:
                            validation = 'El contacto no existe' + ' - ' + str(fila[4])
                            raise ValidationError(validation)
                        rvc_beneficiary_id = self.env['rvc.beneficiary'].create({
                                                            'name': partner_id.name + '-' + 'Derechos de Identificación',
                                                            'partner_id': partner_id.id,
                                                            'vat': partner_id.vat,
                                                            'name_contact': contact_id.name,
                                                            'phone_contact': contact_id.phone,
                                                            'email_contact': contact_id.email,
                                                            'cargo_contact': contact_id.x_contact_job_title.id,
                                                            'active': True})
                        self.env.cr.commit()
                    product_benef = self.env['product.benef'].create({
                                                        'name': partner_id.name + '-' + 'LOGYCA/COLABORA',
                                                        'partner_id': rvc_beneficiary_id.id,
                                                        'parent_id': sponsored_id.id,
                                                        'agreement_id': agreement_rvc_id.id,
                                                        'product_id': product_id.id,
                                                        'sub_product_ids': sub_product_id[0],
                                                        'date_end': '2022-01-31'})
                    cre.append(product_benef.id)
                else:
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
                        validation = 'La empresa Halonadora no existe' + ' - ' + str(fila[1])
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
        print('ERRORES', e)
        if len(e)>1:
            error.append(e)
        print('ERRORES222222', error)
        if error:
            msj='No se puede importar el archivo, contiene los siguientes errores: \n\n'
            for e in error:
                print('ERRORES3333333', e)
                msj+=str(e)
                msj+='\n'
            raise ValidationError(msj)            
        obj_model = self.env['ir.model.data']
        res = obj_model.get_object_reference('rvc', 'product_benef_tree')
        return {
            'name': 'Registros Importados'+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.benef',
            'views': [([res and res[1] or False], 'tree')],
            'domain': [('id','in',cre)],
            'target': 'current'
        }
                    