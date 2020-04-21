# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

#---------------------------Modelo RES-PARTNER / TERCEROS-------------------------------#

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'x_type_thirdparty, x_contact_type, name'
    #INFORMACION BASICA
    name = fields.Char(track_visibility='onchange')
    same_vat_partner_id = fields.Many2one('res.partner', string='Partner with same Tax ID', compute='_compute_no_same_vat_partner_id', store=False)
    x_type_thirdparty = fields.Many2many('logyca.type_thirdparty',string='Tipo de tercero',track_visibility='onchange')
    x_active_for_logyca = fields.Boolean(string='Activo', track_visibility='onchange')
    x_document_type = fields.Selection([
                                        ('11', 'Registro civil de nacimiento'),
                                        ('12', 'Tarjeta de identidad'),
                                        ('13', 'Cédula de ciudadania'),
                                        ('21', 'Tarjeta de extranjería'),
                                        ('22', 'Cedula de extranjería'),
                                        ('31', 'NIT'),
                                        ('41', 'Pasaporte'),
                                        ('42', 'Tipo de documento extranjero'),
                                        ('43', 'Sin identificación del exterior o para uso definido por la DIAN'),
                                        ('44', 'Documento de identificación extranjero persona jurídica')
                                    ], string='Tipo de documento', track_visibility='onchange')
    x_digit_verification = fields.Integer(string='Digito de verificación', track_visibility='onchange',compute='_compute_verification_digit', store=True)
    x_first_name = fields.Char(string='Primer nombre', track_visibility='onchange')
    x_second_name = fields.Char(string='Segundo nombre', track_visibility='onchange')
    x_first_lastname = fields.Char(string='Primer apellido', track_visibility='onchange')
    x_second_lastname = fields.Char(string='Segundo apellido', track_visibility='onchange')
    #x_is_main_contact = fields.Boolean(string='¿Es contacto principal?', track_visibility='onchange')
    x_is_member_directive = fields.Boolean(string='¿Es miembro del Consejo Directivo?', track_visibility='onchange')

    #UBICACIÓN PRINCIPAL
    x_city = fields.Many2one('logyca.city', string='Ciudad', track_visibility='onchange')

    #CLASIFICACION
    x_organization_type = fields.Selection([('1', 'Empresa'),
                                            ('2', 'Universidad'),
                                            ('3', 'Centro de investigación'),
                                            ('4', 'Multilateral'),
                                            ('5', 'Gobierno'),
                                            ('6', 'ONG: Organización no Gubernamental')], string='Tipo de organización', track_visibility='onchange')
    x_work_groups = fields.Many2many('logyca.work_groups', string='Grupos de trabajo', track_visibility='onchange')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', track_visibility='onchange')
    x_ciiu_activity = fields.Many2one('logyca.ciiu', string='Códigos CIIU', track_visibility='onchange')

    #GRUPO EMPRESARIAL
    x_is_business_group = fields.Boolean(string='¿Es un Grupo Empresarial?', track_visibility='onchange')

    #VINCULACION CON logyca
    x_active_vinculation = fields.Boolean(string='Estado de la vinculación', track_visibility='onchange')
    x_text_active_vinculation = fields.Char(string='Vinculación:',compute='_textactive_update', store=False)
    x_date_vinculation = fields.Date(string="Fecha de vinculación", track_visibility='onchange')
    x_type_vinculation = fields.Many2many('logyca.vinculation_types', string='Tipo de vinculación', track_visibility='onchange')
    x_sponsored = fields.Boolean(string='Patrocinado', track_visibility='onchange')
    x_flagging_company = fields.Many2one('res.partner', string='Empresa Jalonadora', track_visibility='onchange')
    x_belongs_academic_allies_cli = fields.Boolean(string='Pertenece a aliados Académicos del CLI', track_visibility='onchange')
    x_belongs_strategic_allies_cli = fields.Boolean(string='Pertenece a aliados Estratégicos del CLI', track_visibility='onchange')
    x_acceptance_data_policy = fields.Boolean(string='Acepta política de tratamiento de datos', track_visibility='onchange')
    x_acceptance_date = fields.Date(string='Fecha de aceptación', track_visibility='onchange')
    x_not_contacted_again = fields.Boolean(string='No volver a ser contactado', track_visibility='onchange')
    x_reason_desvinculation = fields.Selection([
                                        ('1', 'Desvinculado por no pago'),
                                        ('2', 'Desvinculado Voluntariamente'),
                                        ('3', 'Desvinculado por Cesión y/o Fusión'),
                                        ('4', 'Desvinculado por Liquidación de la Empresa'),
                                        ('5', 'Desvinculado por mal uso del sistema')
                                    ], string='Desvinculado por', track_visibility='onchange')
    x_additional_codes  = fields.Boolean(string='¿Maneja Códigos Adicionales?', track_visibility='onchange')
    x_codes_gtin = fields.Boolean(string='¿Maneja Códigos GTIN-8?', track_visibility='onchange')

    #INFORMACION FINANCIERA
    x_asset_range = fields.Many2one('logyca.asset_range', string='Rango de activos', track_visibility='onchange')
    x_income_range = fields.Many2one('logyca.asset_range', string='Rango de ingresos', track_visibility='onchange')
    #x_date_update_asset = fields.Date(string='Fecha de última modificación', compute='_date_update_asset', store=True, track_visibility='onchange')
    x_date_update_asset = fields.Date(string='Fecha de última modificación', track_visibility='onchange')
    x_company_size = fields.Selection([
                                        ('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande')
                                    ], string='Tamaño empresa', track_visibility='onchange')

    #INFORMACION TRIBUTARIA
    x_tax_responsibilities = fields.Many2many('logyca.responsibilities_rut', string='Responsabilidades Tributarias', track_visibility='onchange')

    #INFORMACION COMERCIAL
    x_account_origin = fields.Selection([
                                        ('1', 'Campañas'),
                                        ('2', 'Eventos'),
                                        ('3', 'Referenciado'),
                                        ('4', 'Telemercadeo'),
                                        ('5', 'Web'),
                                        ('6', 'Otro')
                                    ], string='Origen de la cuenta', track_visibility='onchange')
    #x_member_id_team = fields.Many2one('res.users', string='Propietario de la cuenta')

    #INFORMACIÓN CONTACTO
    x_contact_type = fields.Many2many('logyca.contact_types', string='Tipo de contacto', track_visibility='onchange')
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', track_visibility='onchange')
    x_contact_area = fields.Many2one('logyca.areas', string='Área', track_visibility='onchange')
    x_contact_job_title_historic = fields.Char(string='Cargo histórico', track_visibility='onchange')
    x_contact_area_historic = fields.Char(string='Área histórica', track_visibility='onchange')

    #INFORMACION FACTURACION ELECTRÓNICA
    x_email_invoice_electronic = fields.Char(string='Correo electrónico para recepción electrónica de facturas', track_visibility='onchange')

    #INFORMACIÓN EDUCACIÓN - CLIENTES
    X_is_a_student = fields.Boolean(string='¿Es estudiante?', track_visibility='onchange')
    x_educational_institution = fields.Char(string='Institución', track_visibility='onchange')
    x_educational_faculty = fields.Char(string='Facultad', track_visibility='onchange')
    x_taken_courses_logyca = fields.Boolean(string='¿Ha tomado cursos en LOGYCA?', track_visibility='onchange')

    #CAMPOS HISTORICOS
    x_owner_history = fields.Char(string='Propietario historico', track_visibility='onchange')
    x_info_creation_history = fields.Char(string='Información de creación y modificación historica', track_visibility='onchange')
    x_history_partner_notes = fields.One2many('logyca.history_partner_notes', 'partner_id', string = 'Notas')
    x_history_partner_emails = fields.One2many('logyca.history_partner_emails', 'partner_id', string = 'Emails')
    x_history_partner_opportunity = fields.One2many('logyca.history_partner_opportunity', 'partner_id', string = 'Oportunidades')

    @api.depends('x_asset_range')
    def _date_update_asset(self):
        self.x_date_update_asset = fields.Date.today()

    @api.depends('x_active_vinculation')
    def _textactive_update(self):
        for record in self:
            if record.x_active_vinculation:
                self.x_text_active_inculation = 'Activo'
            else:
                self.x_text_active_inculation = 'Inactivo'    

    @api.depends('vat')
    def _compute_no_same_vat_partner_id(self):
        for partner in self:
            partner.same_vat_partner_id = ""

    @api.depends('vat')
    def _compute_verification_digit(self):
        #Logica para calcular digito de verificación
        multiplication_factors = [71, 67, 59, 53, 47, 43, 41, 37, 29, 23, 19, 17, 13, 7, 3]

        for partner in self:
            if partner.vat and partner.x_document_type == '31' and len(partner.vat) <= len(multiplication_factors):
                number = 0
                padded_vat = partner.vat

                while len(padded_vat) < len(multiplication_factors):
                    padded_vat = '0' + padded_vat

                # if there is a single non-integer in vat the verification code should be False
                try:
                    for index, vat_number in enumerate(padded_vat):
                        number += int(vat_number) * multiplication_factors[index]

                    number %= 11

                    if number < 2:
                        self.x_digit_verification = number
                    else:
                        self.x_digit_verification = 11 - number
                except ValueError:
                    self.x_digit_verification = False
            else:
                self.x_digit_verification = False

    #-----------Validaciones
    @api.constrains('vat')
    def check_vatnumber(self):
        for record in self:
            obj = self.search([('x_type_thirdparty','in',[1,3,4]),('vat','=',record.vat),('id','!=',record.id)])
            if obj:
                raise Warning("Advertencia", "Ya existe un Cliente con este número de NIT")