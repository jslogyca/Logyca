# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
import base64
import time
import locale
import json
import re
import requests
import logging
import uuid

_logger = logging.getLogger(__name__)

class BenefitApplication(models.Model):
    _name = 'benefit.application'
    _description = 'Postulación a beneficio'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _default_access_token(self):
        return uuid.uuid4().hex

    state = fields.Selection([('draft', 'Draft'), 
                                    ('notified', 'Notificado'),
                                    ('confirm', 'Aceptado'),
                                    ('rejected', 'Rechazado'),
                                    ('cancel', 'Cancelado'),
                                    ('done', 'Entregado')], string='State', default='draft', readonly=True, track_visibility='onchange')
    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria', track_visibility='onchange')
    parent_id = fields.Many2one('rvc.sponsor', string='Empresa Patrocinadora', track_visibility='onchange')
    product_id = fields.Many2one('product.rvc', string='Producto', track_visibility='onchange')
    name = fields.Char(string='Name', track_visibility='onchange')
    codes_quantity = fields.Integer('Cantidad de Códigos', track_visibility='onchange')
    benefit_type = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], related='product_id.benefit_type', readonly=True, store=True, string="Beneficio", track_visibility='onchange')
    sub_product_ids = fields.Many2one('sub.product.rvc', string='Sub-Productos', track_visibility='onchange')
    date_end = fields.Date(string='Date End', track_visibility='onchange')
    acceptance_date = fields.Datetime(string='Fecha/Hora Aceptación', track_visibility='onchange', readonly=True)
    notification_date = fields.Datetime(string='Fecha/Hora Notificación', track_visibility='onchange', readonly=True)
    rejection_date = fields.Datetime(string='Fecha/Hora Rechazo', track_visibility='onchange', readonly=True)
    gln = fields.Char('Código GLN', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, track_visibility='onchange')
    contact_name = fields.Char('Nombre Contacto', related='partner_id.contact_name', track_visibility='onchange')
    contact_phone = fields.Char('Teléfono Contacto', related='partner_id.contact_phone', track_visibility='onchange')
    contact_email = fields.Char('Email Contacto', related='partner_id.contact_email', track_visibility='onchange')
    contact_position = fields.Char('Cargo Contacto', related='partner_id.contact_position', track_visibility='onchange')
    vat = fields.Char('Número Documento', related='partner_id.vat', track_visibility='onchange')
    access_token = fields.Char('Token', default=_default_access_token, help="Token de acceso para aceptar beneficio desde el correo")

    _sql_constraints = [
        ('benefits_partner_product_uniq', 'unique (partner_id, product_id)', '¡Error Guardando! La empresa seleccionada ya está aplicando para este beneficio.')
    ]

    def name_get(self):
        return [(product.id, '%s - %s' % (product.partner_id.partner_id.name, product.product_id.name)) for product in self]    

    def unlink(self):
        for benefit_application in self:
            if benefit_application.state not in ('draft', 'cancel'):
                raise ValidationError(_('¡Oops! No puede eliminar una postulación que no esté en estado borrador o cancelada.'))
        return super(BenefitApplication, self).unlink()


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_confirm(self):
        for benefit_application in self:
            if benefit_application.state in ('notified'):
                view_id = self.env.ref('rvc.rvc_template_email_confirm_wizard_form').id,
                return {
                    'name':_("Enviar Aceptación"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'rvc.template.email.wizard',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]'
                }
                self.write({'state': 'confirm'})


    def action_done(self):
        for benefit_application in self:
            if benefit_application.state in ('confirm'):
                # validamos que no hayan productos comprados disponibles
                if self.product_id.benefit_type == 'codigos':
                    if self._validate_bought_products():
                        view_id = self.env.ref('rvc.rvc_template_email_done_wizard_form').id,
                        return {
                            'name':_("Enviar Kit de Bienvenida"),
                            'view_mode': 'form',
                            'view_id': view_id,
                            'view_type': 'form',
                            'res_model': 'rvc.template.email.wizard',
                            'type': 'ir.actions.act_window',
                            'nodestroy': True,
                            'target': 'new',
                            'domain': '[]'
                        }
                        self.write({'state': 'done'})
                else:
                    view_id = self.env.ref('rvc.rvc_template_email_done_wizard_form').id,
                    return {
                        'name':_("Enviar Kit de Bienvenida"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'rvc.template.email.wizard',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]'
                    }
                    self.write({'state': 'done'})

    def action_rejected(self):
        for benefit_application in self:
            view_id = self.env.ref('rvc.rvc_template_email_rejected_wizard_form').id,
            return {
                'name':_("Rechazar Beneficio"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'rvc.template.email.wizard',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]'
            }
            self.write({'state': 'rejected', 'rejection_date': datetime.now()})


    def action_re_done(self):
        self.write({'state': 'confirm', 'acceptance_date': datetime.now()})


    def action_notified(self):
        for benefit_application in self:
            #Antes de notificar al beneficiario validamos si beneficio es codigos
            # y si cantidad de codigos es mayor a cero
            # y si no tiene productos comprados disponibles
            if self.product_id.benefit_type == 'codigos' and self._validate_qty_codes() and self._validate_bought_products():
                if benefit_application.state in ('draft', 'notified'):
                    view_id = self.env.ref('rvc.rvc_template_email_wizard_form').id,
                    return {
                        'name':_("Are you sure?"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'rvc.template.email.wizard',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]'
                    }
                    self.write({'state': 'notified', 'notification_date': datetime.now()})
            elif self.product_id.benefit_type != 'codigos':
                raise ValidationError(_('Oops! Muy pronto podrás notificar los beneficios LOGYCA/COLABORA y LOGYCA/ANALÍTICA.\n\n'\
                    'Por el momento solo puedes notificar el beneficio DERECHOS DE IDENTIFICACIÓN.'))
            elif not self._validate_qty_codes():
                logging.warning("===> _validate_qty_codes no pasó la validación")
            elif not self._validate_bought_products():
                logging.warning("===> _validate_bought_products no pasó la validación")

    @api.model
    def create(self, vals):
        if 'partner_id' in vals and 'name' not in vals:
            beneficiary = self.env['rvc.beneficiary'].browse(vals.get('partner_id'))
            vals['name'] = beneficiary.partner_id.vat + '-' + beneficiary.partner_id.name

            if 'product_id' in vals:
                product_id = self.env['product.rvc'].browse(int(vals['product_id']))

                #validar si producto rvc es codigos
                if product_id.code == '01':
                    # validar si tiene códigos comprados
                    self._validate_bought_products_create(beneficiary.partner_id.vat)

        return super(BenefitApplication, self).create(vals)

    def write(self, vals):
        res = super(BenefitApplication, self).write(vals)
        self._validate_gln_only_numbers()
        self._validate_gln()

        if 'state' in vals and vals['state'] != 'done':
            self._validate_bought_products()
        return res

    @api.constrains('gln')
    def _validate_gln_only_numbers(self):
        if self.gln and not re.match(r'^[0-9]+$', str(self.gln)):
            raise ValidationError(_('Código GLN "%s" es inválido.\n\nLos códigos GLN solo están compuestos de números.' % str(self.gln)))
        return True

    def _validate_gln(self):
        available_gln_codes = "No codes"
        gln_from_user_found = False
        qty_codes_found = 0

        if self.partner_id and (self.product_id.benefit_type == 'codigos' or self.product_id.benefit_type == 'colabora'):
            
            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/EmpresaGln/"
            else:
                url = "https://asctestdocker.azurewebsites.net/codes/EmpresaGln/"

            payload = {'nit': str(self.vat)}

            response = requests.get(url, data=json.dumps(payload))
            if response.status_code == 200:
                result = response.json()
                response.close()

                if len(result) > 0:
                    available_gln_codes = ""
                    qty_codes_found = len(result)

                for gln in result:
                    available_gln_codes = available_gln_codes + "\n" + str(gln.get('id'))

                    #caso 1: usuario ingresa un gln
                    if self.gln:
                        #caso 2: usuario ingresa gln y si está registrado.
                        if str(gln.get('id')) == self.gln:
                            gln_from_user_found = True
                            break
                    #caso 5: usuario no ingresa un gln
                    else:
                        # caso 6 y 7: usuario no ingresa gln pero se encontró que hay uno (caso 6) o varios registrados (caso 7).
                        if len(result) >= 1:
                            self.gln = result[0].get('id')
                            return True

            else:
                raise ValidationError(\
                    _('No se ha podido validar el Código GLN de la empresa seleccionada.\
                       Inténtelo nuevamente o comuníquese con soporte. <strong>Error:</strong> %s' % str(response)))

            #caso 3: usuario ingresa gln pero es incorrecto y se encuentra uno válido.
            if self.gln and gln_from_user_found == False and available_gln_codes != "No codes" and qty_codes_found == 1:
                raise ValidationError(\
                    _('El código GLN ingresado es incorrecto, sin embargo encontramos uno registrado:\n\
                        %s \n\nPor favor copie y pegue éste.' % str(available_gln_codes)))
            #caso 4: usuario ingresa gln incorrecto pero hay varios válidos registrados.
            elif self.gln and gln_from_user_found == False and available_gln_codes != "No codes":
                raise ValidationError(\
                    _('El código GLN "%s" no es válido, sin embargo encontramos los siguientes %s códigos registrados: \n\
                        %s \n\nPor favor copie y pegue alguno.' % (self.gln, str(qty_codes_found), str(available_gln_codes))))
            #caso 8: no tiene gln registrado. Registrando uno para la empresa seleccionada.
            elif not self.gln and gln_from_user_found == False and available_gln_codes == "No codes":
                logging.info(" ==> Se asignará GLN con el beneficio <===")

            #caso 9: usuario ingresa GLN pero es incorrecto y no tiene GLN's.
            elif self.gln and gln_from_user_found == False and available_gln_codes == "No codes":
                partner_id = False

                #es un contacto
                if self.partner_id.partner_id.is_company == False or self.partner_id.partner_id.parent_id:
                    partner_id = self.partner_id.partner_id.parent_id
                else:
                    partner_id = self.partner_id.partner_id
                tmp_code = str(self.gln)

                raise ValidationError(\
                    _('El Código GLN "%s" es inválido. La empresa "%s" no tiene código(s) GLN registrados.'\
                    '\n\nPor favor deje el campo Código GLN vacío, le asignaremos uno en la entrega del beneficio.' % (tmp_code, str(partner_id.name))))
                
    def _validate_bought_products(self):
        for benefit_application in self:
            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(self.vat))
            else:
                url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(self.vat))

            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                response.close()

                if result.get('CodigosCompradosDisponibles') > 10:
                     logging.info("CodigosCompradosDisponibles > 10")
                     raise ValidationError(\
                        _('¡Lo sentimos! La empresa %s tiene %s código(s) comprados disponibles.' % (str(self.partner_id.partner_id.vat) + '-' + str(self.partner_id.partner_id.name), str(result.get('CodigosCompradosDisponibles')))))
            else:
                raise ValidationError(\
                        _('No se pudo validar si la empresa seleccionada tiene códigos comprados disponibles.\
                            Inténtelo nuevamente o comuníquese con soporte. <strong>Error:</strong> %s' % (str(response))))
            return True

    # validacion para el create, ya que no tenemos self entonces en esta funcion no se usa self.
    def _validate_bought_products_create(self, vat):
        cr = self._cr
        cr.execute("SELECT value FROM ir_config_parameter WHERE key='web.base.url'")
        query_result = self.env.cr.dictfetchone()

        if query_result['value'] == 'https://logyca.odoo.com':
            url = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(vat))
        else:
            url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(vat))

        response = requests.get(url)

        if response.status_code == 200:
            result = response.json()
            response.close()

            if result.get('CodigosCompradosDisponibles') > 10:
                 raise ValidationError(\
                    _('¡Lo sentimos! La empresa tiene %s código(s) comprados disponibles.') % str(result.get('CodigosCompradosDisponibles')))
        else:
            raise ValidationError(\
                    _('No se pudo validar si la empresa seleccionada tiene códigos comprados disponibles.\
                        Inténtelo nuevamente o comuníquese con soporte. <strong>Error:</strong> %s' % (str(response))))
        return True

    def _validate_qty_codes(self):
        for rec in self:
            if rec.codes_quantity == 0 and self.product_id.benefit_type == 'codigos':
                raise ValidationError(\
                    _('Por favor indique la -Cantidad de Códigos- que se entregará a la empresa beneficiaria.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))
        return True

    def assignate_gln_code(self):
        #creando código
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_assignate = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/assignate/"
        else:
            url_assignate = "https://asctestdocker.azurewebsites.net/codes/assignate/"

        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"1",
            "Request": [{
                "Quantity": 1,
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.partner_id.name,
                "Schema": 2,
                "ScalePrefixes": False,
                "Type": 55603,
                "PrefixType": "",
                "VariedFixedUse": False}],
                "UserName": "Admin"})
        headers_assignate = {'Content-Type': 'application/json'}
        
        #Making http post request
        response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

        if response_assignate.status_code == 200:
            response_assignate.close()
            #marcando código
            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_mark = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/mark/"
            else:
                url_mark = "https://asctestdocker.azurewebsites.net/codes/mark/"            

            body_mark = json.dumps({
                "Nit": self.vat,
                "TipoProducto": 1,
                "Username": "RVC",
                "Esquemas": [
                    2,
                    3,
                    6
                ],
                "Codigos": [
                    {
                        "Descripcion": "Gln Empresa %s" % str(self.partner_id.partner_id.name),
                        "TipoProducto": 4
                    }
                ]
            })
            headers_mark = {'Content-Type': 'application/json'}
            response_mark = requests.post(url_mark, headers=headers_mark, data=body_mark, verify=True)

            if response_mark.status_code == 200:
                response_mark.close()
                result = response_mark.json()

                self.write({'gln': str(result.get('IdCodigos')[0].get('Codigo'))})
                self.message_post(body=_('El Código GLN fue creado y entregado con el beneficio.'))
                logging.info(\
                    "Código GLN '%s' creado y marcado para la empresa %s"\
                        % (result.get('IdCodigos')[0].get('Codigo'), str(self.partner_id.partner_id.name)))
        else:
            self.message_post(body=_('No se pudo asignar al beneficiario un Código GLN. El servidor respondió %s' % str(response_assignate)))

    def assign_identification_codes(self):

        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_assignate = "https://app-asignacioncodigoslogyca-prod-v1.azurewebsites.net/codes/assignate/"
        else:
            url_assignate = "https://asctestdocker.azurewebsites.net/codes/assignate/"        

        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"",
            "Request": [{
                "Quantity": int(self.codes_quantity),
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.partner_id.name,
                "Schema": 2,
                "ScalePrefixes": False,
                "Type": 55600,
                "PrefixType": "",
                "VariedFixedUse": False}],
                "UserName": "Admin"})
        headers_assignate = {'Content-Type': 'application/json'}

        #Making http post request
        response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

        logging.info("====> response_assignate_codes_to_beneficiary =>" + str(response_assignate))

        if response_assignate.status_code == 200:
            #TODO: logging
            response_assignate.close()
            self.message_post(body=_('Los %s Códigos de Identificación fueron entregados al beneficiario' % str(int(self.codes_quantity))))
            return True
        else:
            #TODO: logging
            self.message_post(body=_('Los Códigos de Identificación no pudieron ser entregados al beneficiario. <strong>Error:</strong> %s' % str(response_assignate)))
            return False

    def get_token_assign_credentials(self):
        
        if self.get_odoo_url() == 'https://logyca.odoo.com':
            url_get_token = "http://logycassoapi.azurewebsites.net/api/Token/Authenticate"
        else:
            url_get_token = "http://apiauthenticationssodev.azurewebsites.net/api/Token/Authenticate"
        

        body_get_token = json.dumps({
            "email": "tiendavirtualapi@yopmail.com",
            "password": "Logyca2020"
            })
        headers_get_token = {'Content-Type': 'application/json'}

        response_get_token = requests.post(url_get_token, headers=headers_get_token, data=body_get_token, verify=True)

        if response_get_token.status_code == 200:
            result = response_get_token.json()
            response_get_token.close()

            token = str(result.get('resultToken').get('token'))
            return token

        return False

    def assign_credentials_for_codes(self):
        bearer_token = self.get_token_assign_credentials()

        if bearer_token or bearer_token[0]:
            today_date = datetime.now()
            today_one_year_later = today_date + relativedelta(years=1)

            if self.get_odoo_url() == 'https://logyca.odoo.com':
                url_assignate= "https://logycacolaboraapiv1.azurewebsites.net/api/Company/AddCompanyEcommerce"            
            else:
                url_assignate= "https://logycacolaboratestapi.azurewebsites.net/api/Company/AddCompanyEcommerce"

            body_assignate = json.dumps({
                    "Nit": self.vat,
                    "Name": self.contact_name,
                    "UserMail": self.contact_email,
                    "InitialDate": today_date.strftime('%Y-%m-%d'),
                    "EndDate": today_one_year_later.strftime('%Y-%m-%d'),
                    "level": 0,
                    "TypeService": 1,
                    "NumberOverConsumption": 0,
                    "IsOverconsumption": False
                })
            headers_assignate = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % bearer_token}

            #Making http post request
            response_assignate = requests.post(url_assignate, headers=headers_assignate, data=body_assignate, verify=True)

            logging.info("====> response_assignate_credentials =>" + str(response_assignate))

            if response_assignate.status_code == 200:
                #TODO: logging
                result = response_assignate.json()
                response_assignate.close()

                #error al crear credenciales
                if result.get('dataError') == True:
                    #TODO: logging
                    error_message = result.get('apiException').get('message')
                    if not error_message:
                        error_message = result.get('resultMessage')
                    self.message_post(body=_(\
                        'No pudieron asignarse las credenciales para acceder a la administración de códigos.'\
                            '\n<strong>Error:</strong> %s' % str(error_message)))
                else:
                    self.message_post(body=_('Las credenciales para acceder a la administración de códigos fueron entregadas con el beneficio.'))
                    return True
            else:
                #TODO: logging
                logging.exception("====> assign_credentials_for_codes =>" + str(response_assignate))
                logging.exception("====> assign_credentials_for_codes =>" + str(response_assignate.text))
                self.message_post(body=_(\
                        'No pudieron asignarse las credenciales. <strong>Error:</strong> %s' % str(response_assignate)))
                return False
        else:
            self.message_post(body=_("No pudo obtenerse el token para realizar la asignación de credenciales en Colabora."\
                                     "Inténtelo nuevamente o comuníquese con soporte."))
            return False

    def today_date_spanish(self):
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        return datetime.now().strftime('%d de %B de %Y')

    def update_contact(self, company_id):
        type_id = self.env.ref('rvc.contact_types_rvc').id,
        self._cr.execute(''' SELECT id FROM res_partner WHERE email=%s AND is_company IS False
                                AND parent_id=(SELECT id FROM res_partner WHERE vat=%s AND is_company IS True) ''',
                                            (company_id.contact_email, company_id.vat))
        contact_id= self._cr.fetchone()
        if contact_id and contact_id[0]:
            self._cr.execute(\
                ''' SELECT * FROM logyca_contact_types_res_partner_rel WHERE res_partner_id=%s AND logyca_contact_types_id=%s ''', (contact_id[0], type_id))
            type_contact = self._cr.fetchone()
            if not type_contact:
                self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel
                                        (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_id[0], type_id))
        else:
            contact_new = self.env['res.partner'].create({
                                        'name': company_id.contact_name,
                                        'street': company_id.partner_id.street,
                                        'country_id': company_id.partner_id.country_id.id,
                                        'state_id': company_id.partner_id.state_id.id,
                                        'email': company_id.contact_email,
                                        'phone': company_id.contact_phone,
                                        'vat': company_id.vat,
                                        'parent_id': company_id.partner_id.id,
                                        'x_city': company_id.partner_id.x_city.id})
            self._cr.execute(''' INSERT INTO logyca_contact_types_res_partner_rel
                                    (res_partner_id, logyca_contact_types_id) SELECT %s, %s ''', (contact_new.id, type_id))
        return True

    def update_company(self, company_id):
        self._cr.execute(''' UPDATE res_partner SET x_sponsored=%s, x_flagging_company=%s WHERE id=%s ''',
                                        (True, company_id.parent_id.partner_id.id, company_id.partner_id.partner_id.id))
        return True

    def _add_vinculation_partner(self):
        try:
            partner_id = self.partner_id.partner_id
            vinculation_99_anos_id = self.env['logyca.vinculation_types'].search([('name','=','99 Años')],limit=1)
            # si el partner no tiene una vinculación activa entonces lo vinculamos como 99 anios
            if partner_id.x_active_vinculation == False:
                partner_id.x_type_vinculation = [(6,0, vinculation_99_anos_id.ids)]
                partner_id.x_active_vinculation = True
                partner_id.x_date_vinculation = date.today()
                self.message_post(body=_(\
                            'Se activó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
            # si tiene una vinculacion activa entonces le adicionamos la 99 anios
            else:
                # si tiene al menos un tipo de vinculacion entonces revisamos cuáles son
                if partner_id.x_type_vinculation:
                    vinculated = True
                    for vinculation in partner_id.x_type_vinculation:
                        # tiene la vinculación 'no tiene vinculacion' o tiene la '99 anos'
                        if vinculation.code in ('12', '10'):
                            #reemplazamos la vinculacion por la '99 anos' y a fecha activacion sera hoy
                            partner_id.x_type_vinculation = [(6,0, vinculation_99_anos_id.ids)]
                            partner_id.x_date_vinculation = date.today()
                            self.message_post(body=_(\
                            'Se activó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
                        else:
                            #agregamos la vinculacion 99 anios y ponemos fecha activacion hoy
                            partner_id.x_type_vinculation = [(4, vinculation_99_anos_id.ids)]
                            partner_id.x_date_vinculation = date.today()
                            self.message_post(body=_(\
                                        'Se adicionó la vinculación: <strong>%s</strong>' % str(vinculation_99_anos_id.name)))
        except Exception as e:
            self.message_post(body=_(\
                '<strong>¡Error!</strong> No se pudo activar la vinculación <strong>%s</strong>. Descripción: %s' % (str(vinculation_99_anos_id.name), str(e))))


    def _cron_send_welcome_kit(self):
        logging.warning("==> Iniciando cron de enviar kits de bienvenida ...")

        if not self:
            counter = 0
            self = self.search([('state', '=', 'confirm')])

            for postulation_id in self:
                counter =+ 1
                # limitamos el envío de kits para no saturar el servidor.
                if counter < 30:
                    if postulation_id.partner_id.contact_email:
                        access_link = postulation_id.partner_id.partner_id._notify_get_action_link('view')
                        template = self.env.ref('rvc.mail_template_welcome_kit_rvc')
                        template.with_context(url=access_link).send_mail(postulation_id.id, force_send=True)

                        if not postulation_id.gln:
                            # si no tiene GLN, asignamos uno.
                            postulation_id.assignate_gln_code()

                        # Asignar beneficio de códigos de identificación
                        if postulation_id.assign_identification_codes():
                            postulation_id.assign_credentials_for_codes()

                        # Actualizar Contacto y Empresa
                        self.update_contact(postulation_id.partner_id)
                        if postulation_id.parent_id:
                            self.update_company(postulation_id)

                        # Agregar tipo de vinculacion al tercero
                        self._add_vinculation_partner()

                        postulation_id.write({'state': 'done'})
                        counter += 1
                    else:
                        raise ValidationError(_('La empresa seleccionada no tiene email.'))
                else:
                    logging.exception("====> Cron alcanzó el límite de kits a enviar, esperando la próxima ejecución para enviar más...")

    def _cron_mark_as_rejected(self):
        logging.warning("==> Iniciando cron de marcar postulaciones como rechazadas ...")

        if not self:
            self = self.search([('state', '=', 'notified'), ('notification_date', '<', datetime.now() - relativedelta(days=31))])  
            
            for postulation_id in self:
                postulation_id.write({'state': 'rejected', 'rejection_date': datetime.now()})
                #TODO: logging
    
    
    def attach_OM_2_partner(self, postulation_id):

        pdf = self.env.ref('rvc.action_report_rvc').render_qweb_pdf(postulation_id.id)
        b64_pdf = base64.b64encode(pdf[0])

        attachment = self.env['ir.attachment'].create({
            'name': "Oferta Mercantil RVC.pdf",
            'type': 'binary',
            'datas': b64_pdf,
            'res_model':'res.partner',
            'res_id': postulation_id.partner_id.partner_id.id
        })
        if not attachment:
            return True 
        return False

    def send_notification_benefit(self):
        for benefit_admon in self:
            partner=self.env['res.partner'].search([('id','=',benefit_admon.partner_id.partner_id.id)])
            if partner and benefit_admon.partner_id.contact_email:
                access_link = partner._notify_get_action_link('view')
                template = self.env.ref('rvc.mail_template_deactivated_partner_benef')
                template.with_context(url=access_link).send_mail(benefit_admon.id, force_send=False)
                benefit_admon.write({'state': 'notified', 'notification_date': datetime.now()})

    def get_odoo_url(self):
        return self.env['ir.config_parameter'].sudo().get_param('web.base.url')
