# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import json
import re
import requests
import logging

_logger = logging.getLogger(__name__)

class BenefitsAdmon(models.Model):
    _name = 'benefits.admon'
    _description = 'Benefits Administration.'
    _inherit = ['mail.thread', 'mail.activity.mixin']


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

    _sql_constraints = [
        ('benefits_partner_product_uniq', 'unique (partner_id, product_id)', '¡Error Guardando! La empresa seleccionada ya está aplicando para este beneficio.')
    ]

    def name_get(self):
        return [(product.id, '%s - %s' % (product.partner_id.partner_id.name, product.product_id.name)) for product in self]    

    def unlink(self):
        for benefits_admon in self:
            if benefits_admon.state not in ('draft', 'cancel'):
                raise ValidationError(_('You cannot delete an Benef which is not draft or cancelled. You should create a credit note instead.'))
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
                    if self._validate_qty_codes() and self._validate_bought_products():
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
                response_mark = response_mark.json()
                self.write({'gln': str(response_mark.get('IdCodigos')[0].get('Codigo'))})
                self.message_post(body=_('El Código GLN fue creado y entregado con el beneficio.'))
                logging.info("Código GLN '%s' creado y marcado para la empresa %s" % (response_mark.get('IdCodigos')[0].get('Codigo'), str(self.partner_id.name)))
