# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from psycopg2 import IntegrityError
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

class RVCImportFileWizard(models.TransientModel):
    _name = 'rvc.import.file.wizard'
    _description = 'Cargue Masivo de Postulaciones a Beneficios'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    benefit_type = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Logyca Colabora'),
                                    ('analitica', 'Logyca Analítica')], string="Beneficio")
    
    def validate_mail(self, email):
        if email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(email.lower()))
        if match == None:
            return False
        return True

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
            if fila[0] and fila[1]:
                
                if self.benefit_type == 'codigos':
                    # Validar con el nit de la empresa beneficiaria que esté registrado en Odoo
                    partner_id=self.env['res.partner'].search([('vat','=',str(fila[0])), ('is_company','=',True)])

                    if len(partner_id) == 0:
                        partner_id=self.env['res.partner'].search([('x_type_thirdparty','=',1),('vat','=', str(fila[0]))])

                    if len(partner_id) > 1:
                        partner_id=self.env['res.partner'].search([('vat','=',str(fila[0]))])[0]

                    if not partner_id:
                        validation = 'Fila %s: La empresa beneficiaria con NIT %s no existe en Odoo' % (str(count), str(fila[0]))
                        errors.append(validation)
                        continue

                    # Validar que el tipo de vinculación de la empresa beneficiaria no sea miembro, ni cliente CE
                    if partner_id.x_type_vinculation:
                        member_or_ce = False
                        for vinculation in partner_id.x_type_vinculation:
                            if vinculation.code in ('01', '02'):
                                member_or_ce = True
                                validation = 'Fila %s: %s no aplica para el beneficio. Es miembro o cliente CE' %\
                                        (str(count), partner_id.vat + '-' + str(partner_id.name.strip()))
                                errors.append(validation)
                        if member_or_ce:
                            continue

                    #si se ingresa correo electrónico del contacto
                    if fila[4]:
                        #si no es un email válido
                        if self.validate_mail(str(fila[4])) == False:
                            validation = 'Fila %s: %s tiene un email de contacto no válido (%s)' %\
                                (str(count), str(partner_id.vat + '-' + partner_id.name.strip()).upper(), str(fila[4]))
                            errors.append(validation)
                            continue
                    else:
                        validation = 'Fila %s: %s no tiene email de contacto' %\
                                (str(count), str(partner_id.vat + '-' + partner_id.name.strip()).upper())
                        errors.append(validation)
                        continue

                    #buscando el registro de la empresa como beneficiaria
                    rvc_beneficiary_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id)])

                    if not rvc_beneficiary_id:
                        try:
                            with self._cr.savepoint():
                                rvc_beneficiary_id = self.env['rvc.beneficiary'].create({
                                                                    'partner_id': partner_id.id,
                                                                    'vat': partner_id.vat,
                                                                    'contact_name': str(fila[3]),
                                                                    'contact_phone': str(fila[5]),
                                                                    'contact_email': str(fila[4]).strip().lower(),
                                                                    'contact_position': str(fila[6]),
                                                                    'active': True})
                                self.env.cr.commit()
                        except Exception as e:
                            validation = "Fila %s: %s no se pudo crear como empresa beneficiaria. %s" % (str(count), partner_id.vat + '-' + str(partner_id.name.strip()),str(e))
                            errors.append(validation)
                            continue
                        except IntegrityError:
                            self.env.cr.rollback()
                    else:
                        #beneficiario existe entonces traemos el registro.
                        rvc_beneficiary_id=self.env['rvc.beneficiary'].browse(rvc_beneficiary_id.id)

                    #beneficio
                    product_id=self.env['product.rvc'].search([('benefit_type','=',self.benefit_type)])

                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    if rvc_beneficiary_id:
                        benefit_application_id=self.env['benefit.application'].search([('partner_id','=',rvc_beneficiary_id.id),('product_id','=',product_id.id)])
                        if benefit_application_id:
                            validation = 'Fila %s:  %s ya tiene una entrega de beneficio activa'\
                                    % (str(count), str(partner_id.vat + '-' + partner_id.name.strip()).upper())
                            errors.append(validation)
                            continue

                    # Validar que la empresa beneficiaria esté activa
                    if not partner_id.active:
                        validation = 'Fila %s: La empresa beneficiaria %s con NIT %s no esta activa' % (str(count), str(partner_id.name).strip(), str(fila[0]))
                        errors.append(validation)
                        continue

                    # Validar que el tamaño de la empresa beneficiaria sea micro, pequeña o mediana (MIPYME)
                    if partner_id.x_company_size == '4':
                        validation = 'Fila %s: El tamaño de la empresa beneficiaria %s no es micro, pequeña o mediana (MIPYME)' %\
                            (str(count), partner_id.vat + '-' + str(partner_id.name.strip()))
                        errors.append(validation)
                        continue

                    #empresa patrocinadora
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)

                    #patrocinadora como halonadora rvc
                    sponsored_id=self.env['rvc.sponsor'].search([('partner_id','=',parent_id.id)])

                    if not sponsored_id:
                        validation = 'Fila %s: La empresa Halonadora con NIT %s no existe' % (str(count), str(fila[1]))
                        errors.append(validation)
                        continue
                    

                    if rvc_beneficiary_id and rvc_beneficiary_id.id:
                        try:
                            vals = {
                                'partner_id': rvc_beneficiary_id.id,
                                'parent_id': sponsored_id.id,
                                'product_id': product_id.id,
                                'codes_quantity': int(fila[2])
                            }
                            benefit_application = self.env['benefit.application'].sudo().create(vals)
                            
                            if benefit_application:
                                self.env.cr.commit()
                                cre.append(benefit_application.id)
                                validation = "Fila %s: %s postulación creada correctamente" % (str(count), str(partner_id.vat + '-' + partner_id.name.strip()).upper())
                                errors.append(validation)
                        except Exception as e:
                            validation = "Fila %s: %s no se puede crear. Error: %s" %\
                                (str(count), str(partner_id.vat + '-' + partner_id.name.strip()).upper(), str(e))
                            errors.append(validation)
                            continue
                    else:
                        logging.warning("=================> no entra a la creacion de benefit.application")

                elif self.benefit_type == 'colabora':
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
                    product_id=self.env['product.rvc'].search([('benefit_type','=',self.benefit_type)])
                    self._cr.execute(\
                        ''' SELECT id FROM sub_product_rvc WHERE product_id=%s AND %s between min_qty AND max_qty and state=%s''',
                            (product_id.id, int(fila[2]), 'activo'))
                    sub_product_id = self._cr.fetchone()
                    if not sub_product_id:
                        validation = 'No existe un subnivel COLABORA configurado para ' + ' - ' + str(fila[2])
                        raise ValidationError(validation)                        
                    parent_id=self.env['res.partner'].search([('vat','=',str(fila[1])), ('is_company','=',True)], limit=1)
                    sponsored_id=self.env['rvc.sponsor'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Halonadora no existe' + ' - ' + str(fila[1])
                        raise ValidationError(validation)
                    rvc_beneficiary_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id)])
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    if rvc_beneficiary_id:
                        benefit_application_id=self.env['benefit.application'].search([('partner_id','=',rvc_beneficiary_id.id),('product_id','=',product_id.id)])
                        if benefit_application_id:
                            validation = 'La empresa Beneficiaria ya tiene una entrega de beneficio activa' + ' - ' + str(fila[0] + ' - ' + partner_id.name)
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
                                                            'contact_name': contact_id.name,
                                                            'contact_phone': contact_id.phone,
                                                            'contact_email': contact_id.email,
                                                            'contact_position': contact_id.x_contact_job_title.id,
                                                            'active': True})
                        self.env.cr.commit()
                    benefit_application = self.env['benefit.application'].create({
                                                        'name': partner_id.name + '-' + 'LOGYCA/COLABORA',
                                                        'partner_id': rvc_beneficiary_id.id,
                                                        'parent_id': sponsored_id.id,
                                                        'product_id': product_id.id,
                                                        'sub_product_ids': sub_product_id[0],
                                                        'date_end': '2022-01-31'})
                    cre.append(benefit_application.id)
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
                        validation = 'el tamaño de la empresa beneficiaria no es micro o pequeña (MIPY)' + ' - ' + str(fila[0])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue                        
                    # Validar que la empresa beneficiaria no tenga otra postulación o entrega activa de este beneficio
                    benf_id=self.env['rvc.beneficiary'].search([('partner_id','=',partner_id.id),('benefit_type','=',self.benefit_type)])
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
                    sponsored_id=self.env['rvc.sponsor'].search([('partner_id','=',parent_id.id)])
                    if not sponsored_id:
                        validation = 'La empresa Halonadora no existe' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue
                    # Validar que el patrocinador no tenga otra postulación o entrega activa de este beneficio para otra empresa beneficiaria
                    benf_patro_id=self.env['rvc.beneficiary'].search([('parent_id','=',parent_id.id),('benefit_type','=',self.benefit_type)])
                    if not benf_patro_id:
                        validation = 'El patrocinador tiene otra postulación o entrega activa de este beneficio'\
                            'para otra empresa beneficiaria' + ' - ' + str(fila[1])
                        self.env['log.import.rvc'].create({
                                                            'name': validation,
                                                            'date_init': fields.Datetime.now(),
                                                            'user_id' : self.env.user.id})
                        continue 

                    rvc_benf = self.env['rvc.beneficiary'].create({
                                                        'name': partner_id.name + '-' + 'Identificación de Productos',
                                                        'partner_id': partner_id.id,
                                                        'contact_name': str(fila[4]),
                                                        'codes_quantity': str(fila[2]),
                                                        'parent_id' : sponsored_id.partner_id.id,
                                                        'state': 'confirm',
                                                        'benefit_type' : self.benefit_type})
                    cre.append(rvc_benf.id)
                    self.env.cr.commit()
        if len(errors)>1:
            error.append(errors)
        if error:
            msj='El resultado de la importación es: \n\n'
            for e in errors:
                msj+=str(e)
                msj+='\n\n'

            raise ValidationError(msj)            
        obj_model = self.env['ir.model.data']
        res = obj_model.get_object_reference('rvc', 'benefit_application_tree')

        if not cre:
            raise UserError(_("No se importaron postulaciones a beneficios RVC."))
        return {
            'name': 'Registros Importados '+str(datetime.now().date().strftime("%d/%m/%Y")),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'benefit.application',
            'views': [([res and res[1] or False], 'tree')],
            'domain': [('id','in',cre)],
            'target': 'current'
        }
