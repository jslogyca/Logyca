# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
import locale
import json
import re
import requests
import logging
import uuid

_logger = logging.getLogger(__name__)

class BenefitsAdmon(models.Model):
    _name = 'benefits.admon'
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
    parent_id = fields.Many2one('rvc.sponsored', string='Empresa Patrocinadora', track_visibility='onchange')
    product_id = fields.Many2one('product.rvc', string='Producto', track_visibility='onchange')
    name = fields.Char(string='Name', track_visibility='onchange')
    codes_quantity = fields.Float('Cantidad de Códigos', track_visibility='onchange')
    benefit_type = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], related='product_id.benefit_type', readonly=True, store=True, string="Beneficio", track_visibility='onchange')
    sub_product_ids = fields.Many2one('sub.product.rvc', string='Sub-Productos', track_visibility='onchange')
    date_end = fields.Date(string='Date End', track_visibility='onchange')
    gln = fields.Char('Código GLN', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, track_visibility='onchange')
    contact_name = fields.Char('Nombre del contacto', related='partner_id.contact_name', track_visibility='onchange')
    contact_phone = fields.Char('Phone', related='partner_id.contact_phone', track_visibility='onchange')
    contact_email = fields.Char('Email', related='partner_id.contact_email', track_visibility='onchange')
    contact_position = fields.Char('Cargo', related='partner_id.contact_position', track_visibility='onchange')
    vat = fields.Char('Número de documento', related='partner_id.vat', track_visibility='onchange')
    access_token = fields.Char('Token', default=_default_access_token, help="Token de acceso para aceptar beneficio desde el correo")

    _sql_constraints = [
        ('benefits_partner_product_uniq', 'unique (partner_id, product_id)', '¡Error Guardando! La empresa seleccionada ya está aplicando para este beneficio.')
    ]

    def name_get(self):
        return [(product.id, '%s - %s' % (product.partner_id.partner_id.name, product.product_id.name)) for product in self]    

    def unlink(self):
        for benefits_admon in self:
            if benefits_admon.state not in ('draft', 'cancel'):
                raise ValidationError(_('¡Oops! No puede eliminar una postulación que no esté en estado borrador o cancelada.'))
        return super(BenefitsAdmon, self).unlink()


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_confirm(self):
        for benefits_admon in self:
            if benefits_admon.state in ('notified'):
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
        for benefits_admon in self:
            if benefits_admon.state in ('confirm'):
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
        for benefits_admon in self:
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
        self.write({'state': 'rejected'})


    def action_re_done(self):
        self.write({'state': 'confirm'})


    def action_notified(self):
        for benefits_admon in self:
            #Antes de notificar al beneficiario validamos si beneficio es codigos
            # y si cantidad de codigos es mayor a cero
            if self.product_id.benefit_type == 'codigos' and self._validate_qty_codes():
                if benefits_admon.state in ('draft', 'notified'):
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
                self.write({'state': 'notified'})

    @api.model
    def create(self, vals):
        res = super(BenefitsAdmon, self).create(vals)
        res._validate_gln_only_numbers()
        res._validate_gln()
        res._validate_bought_products()
        return res

    def write(self, vals):
        res = super(BenefitsAdmon, self).write(vals)
        self._validate_gln_only_numbers()
        self._validate_gln()

        if 'state' in vals and vals['state'] != 'done':
            self._validate_bought_products()
        return res

    def _validate_gln_only_numbers(self):
        if self.gln and not re.match(r'^[0-9]+$', str(self.gln)):
            raise ValidationError(_('Código GLN "%s" es inválido.\n\nLos códigos GLN solo están compuestos de números.' % str(self.gln)))
        return True

    def _validate_gln(self):
        available_gln_codes = "No codes"
        found = False
        qty_codes_found = 0

        if self.partner_id and (self.product_id.benefit_type == 'codigos' or self.product_id.benefit_type == 'colabora'):
            
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
                            found = True
                            break
                    #caso 5: usuario no ingresa un gln
                    else:
                        # caso 6: usuario no ingresa gln pero se encontró que hay uno registrado.
                        if len(result) == 1:
                            self.gln = result[0].get('id')
                            return True

            #caso 3: usuario ingresa gln pero es incorrecto y se encuentra uno válido.
            if self.gln and found == False and available_gln_codes != "No codes" and qty_codes_found == 1:
                raise ValidationError(\
                    _('El código GLN ingresado es incorrecto, sin embargo encontramos uno registrado:\n\
                        %s \n\nPor favor copie y pegue éste.' % str(available_gln_codes)))
            #caso 4: usuario ingresa gln incorrecto pero hay varios válidos registrados.
            elif self.gln and found == False and available_gln_codes != "No codes":
                raise ValidationError(\
                    _('El código GLN "%s" no es válido, sin embargo encontramos los siguientes %s códigos registrados: \n\
                        %s \n\nPor favor copie y pegue alguno.' % (self.gln, str(qty_codes_found), str(available_gln_codes))))
            #caso 7: usuario no ingresa gln pero hay varios registrados.
            if not self.gln and found == False and available_gln_codes != "No codes":
                raise ValidationError(\
                    _('Usted no ingresó un código GLN, sin embargo encontramos los siguientes %s códigos registrados: \n\
                        %s \n\nPor favor copie y pegue alguno.' % (str(qty_codes_found), str(available_gln_codes))))
            #caso 8: no tiene gln registrado. Registrando uno para la empresa seleccionada.
            elif not self.gln and found == False and available_gln_codes == "No codes":
                logging.info(" ==> Asignando GLN (en Desarollo) <===")

            #caso 9: usuario ingresa GLN pero es incorrecto y no tiene GLN's.
            elif self.gln and found == False and available_gln_codes == "No codes":
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
        #url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str("10203040"))
        url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(self.vat))

        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            response.close()
            
            if result.get('CodigosCompradosDisponibles') > 0:
                 raise ValidationError(\
                    _('¡Lo sentimos! La empresa seleccionada tiene %s código(s) comprados disponibles.' % (str(result.get('CodigosCompradosDisponibles')))))
        return True

    def _validate_qty_codes(self):
        for rec in self:
            if rec.codes_quantity == 0:
                raise ValidationError(\
                    _('Por favor indique la -Cantidad de Códigos- que se entregará a la empresa beneficiaria.\n\nEmpresa: %s' % (str(self.partner_id.partner_id.name))))
        return True

    def assignate_gln_code(self):
        #creando código
        url_assignate = "https://asctestdocker.azurewebsites.net/codes/assignate/"
        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"1",
            "Request": [{
                "Quantity": 1,
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.name, 
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
                        "Descripcion": "Gln Empresa %s" % str(self.partner_id.name),
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

    def assign_identification_codes(self):
        url_assignate = "https://asctestdocker.azurewebsites.net/codes/assignate/"
        body_assignate = json.dumps({
            "AgreementName":"",
            "IdAgreement":"",
            "Request": [{
                "Quantity": int(self.codes_quantity),
                "Nit": self.vat,
                "PreferIndicatedPrefix": False,
                "BusinessName": self.partner_id.name,
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
            return False

    def get_token_assign_credentials(self):
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

        if bearer_token:
            today_date = datetime.now()
            today_one_year_later = today_date + relativedelta(years=1)

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

    def _cron_send_welcome_kit(self):
        if not self:
            self = self.search([('state', '=', 'confirm')])
            logging.info("=====> %s" % str(self))

            for postulation_id in self:

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

                    postulation_id.write({'state': 'done'})
                else:
                    raise ValidationError(_('La empresa seleccionada no tiene email.'))
