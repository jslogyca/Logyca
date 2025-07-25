# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

#---------------------------Modelo RES-PARTNER / TERCEROS-------------------------------#

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _order = 'name'
    #TRACK VISIBILITY OLD FIELDS
    street = fields.Char(tracking=True)
    country_id = fields.Many2one(tracking=True)
    state_id = fields.Many2one(tracking=True)
    zip = fields.Char(tracking=True)
    phone = fields.Char(tracking=True)
    mobile = fields.Char(tracking=True)
    email = fields.Char(tracking=True)
    website = fields.Char(tracking=True)
    lang = fields.Selection(tracking=True)
    category_id = fields.Many2many(tracking=True)
    user_id = fields.Many2one(tracking=True)
    property_payment_term_id = fields.Many2one(tracking=True)
    property_product_pricelist = fields.Many2one(tracking=True)
    property_account_position_id = fields.Many2one(tracking=True)
    property_supplier_payment_term_id = fields.Many2one(tracking=True)
    property_purchase_currency_id = fields.Many2one(tracking=True)
    property_account_receivable_id = fields.Many2one(tracking=True)
    property_account_payable_id = fields.Many2one(tracking=True)
    comment = fields.Text(tracking=True)

    #INFORMACION BASICA
    name = fields.Char(tracking=True)
    # same_vat_partner_id = fields.Many2one('res.partner', string='Partner with same Tax ID', compute='_compute_no_same_vat_partner_id', store=False)
    same_vat_partner_id = fields.Many2one('res.partner', string='Partner with same Tax ID', store=False)
    x_type_thirdparty = fields.Many2many('logyca.type_thirdparty',string='Tipo de tercero',tracking=True, ondelete='restrict')
    x_active_for_logyca = fields.Boolean(string='Activo', tracking=True, default=True)
    active_logyca = fields.Boolean(string='Activo', tracking=True, default=True, compute='_depends_active')
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
                                    ], string='Tipo de documento', tracking=True)
    x_digit_verification = fields.Integer(string='Digito de verificación', tracking=True,compute='_compute_verification_digit', store=True)
    x_first_name = fields.Char(string='Primer nombre', tracking=True)
    x_second_name = fields.Char(string='Segundo nombre', tracking=True)
    x_first_lastname = fields.Char(string='Primer apellido', tracking=True)
    x_second_lastname = fields.Char(string='Segundo apellido', tracking=True)
    #x_is_main_contact = fields.Boolean(string='¿Es contacto principal?', tracking=True)
    x_collaborative_group_ids = fields.Many2many(comodel_name='collaborative.group', string='Grupos Colaborativos')

    #UBICACIÓN PRINCIPAL
    x_city = fields.Many2one('logyca.city', string='Ciudad', tracking=True, ondelete='restrict', domain="[('state_id', '=', state_id)]")

    #CLASIFICACION
    x_organization_type = fields.Selection([('1', 'Empresa'),
                                            ('2', 'Universidad'),
                                            ('3', 'Centro de investigación'),
                                            ('4', 'Multilateral'),
                                            ('5', 'Gobierno'),
                                            ('6', 'ONG: Organización no Gubernamental')], string='Tipo de organización', tracking=True)
    x_work_groups = fields.Many2many('logyca.work_groups', string='Grupos de trabajo', tracking=True, ondelete='restrict')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', tracking=True, ondelete='restrict')
    x_ciiu_activity = fields.Many2one('logyca.ciiu', string='Códigos CIIU', tracking=True, ondelete='restrict')

    #GRUPO EMPRESARIAL
    x_is_business_group = fields.Boolean(string='¿Es un Grupo Empresarial?', tracking=True)
    x_name_business_group = fields.Char(string='Nombre Grupo Empresarial', tracking=True)

    #VINCULACION CON logyca
    x_active_vinculation = fields.Boolean(string='Estado de la vinculación', tracking=True)
    x_date_vinculation = fields.Date(string="Fecha de vinculación", tracking=True)
    x_type_vinculation = fields.Many2many('logyca.vinculation_types', string='Tipo de vinculación', tracking=True, ondelete='restrict')
    x_excluded_massive_invoicing = fields.Boolean(string='¿Empresa que se excluye del proceso de facturación masiva?', tracking=True)
    x_gtin_massive_invoicing = fields.Boolean(string='¿Empresa especial GTIN8 incluida en facturación masiva?', tracking=True)
    #Campos RVC
    x_sponsored = fields.Boolean(string='Patrocinado', tracking=True)
    x_flagging_company = fields.Many2one('res.partner', string='Empresa Jalonadora', tracking=True)
    x_rvc_information = fields.One2many('logyca.rvc_information', 'partner_id', string = 'Productos adquiridos', tracking=True)
    #Campos Informativos
    x_is_member_directive = fields.Boolean(string='¿Es miembro del Consejo Directivo?', tracking=True)
    x_is_on_board_of_directors = fields.Boolean(string='¿Pertenece a la junta directiva?', tracking=True)
    x_belongs_academic_allies_cli = fields.Boolean(string='Pertenece a aliados Académicos del CLI', tracking=True)
    x_belongs_strategic_allies_cli = fields.Boolean(string='Pertenece a aliados Estratégicos del CLI', tracking=True)    
    x_meeting_logyca_investigation = fields.Boolean(string='Pertenece a la Junta LOGYCA INVESTIGACIÓN', tracking=True)    
    x_acceptance_data_policy = fields.Boolean(string='Acepta política de tratamiento de datos', tracking=True)
    x_acceptance_date = fields.Date(string='Fecha de aceptación', tracking=True)
    x_not_contacted_again = fields.Boolean(string='No volver a ser contactado total', help="Prohibido enviar información referente a LOGYCA", tracking=True)
    x_not_contacted_again_partially = fields.Boolean(string='No volver a ser contactado parcial', help="Prohibido enviar información comercial, eventos, formaciones, campañas", tracking=True)
    x_date_decoupling = fields.Date(string="Fecha de desvinculación", tracking=True)
    x_reason_desvinculation = fields.Selection([
                                        ('1', 'Desvinculado por no pago'),
                                        ('2', 'Desvinculado Voluntariamente'),
                                        ('3', 'Desvinculado por Cesión y/o Fusión'),
                                        ('4', 'Desvinculado por Liquidación de la Empresa'),
                                        ('5', 'Desvinculado por mal uso del sistema'),
                                        ('6', 'Desvinculado por migración 2020')
                                    ], string='Desvinculado por', tracking=True)
    x_reason_desvinculation_text = fields.Text(string='Observaciones desvinculación') 
    x_additional_codes  = fields.Boolean(string='¿Maneja Códigos Adicionales?', tracking=True)
    x_codes_gtin = fields.Boolean(string='¿Maneja Códigos GTIN-8?', tracking=True)

    #INFORMACION FINANCIERA
    x_asset_range = fields.Many2one('logyca.asset_range', string='Rango de activos', tracking=True, ondelete='restrict')
    x_date_update_asset = fields.Date(string='Fecha de última modificación', compute='_date_update_asset', store=True, tracking=True)
    #x_date_update_asset = fields.Date(string='Fecha de última modificación', tracking=True)
    x_company_size = fields.Selection([
                                        ('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')
                                    ], string='Tamaño empresa', tracking=True)

    #INFORMACION TRIBUTARIA
    x_tax_responsibilities = fields.Many2many('logyca.responsibilities_rut', string='Responsabilidades Tributarias', tracking=True, ondelete='restrict')

    #INFORMACION COMERCIAL
    x_account_origin = fields.Selection([
                                        ('1', 'Campañas'),
                                        ('2', 'Eventos'),
                                        ('3', 'Referenciado'),
                                        ('4', 'Telemercadeo'),
                                        ('5', 'Web'),
                                        ('6', 'Otro')
                                    ], string='Origen de la cuenta', tracking=True)
    #x_member_id_team = fields.Many2one('res.users', string='Propietario de la cuenta')

    #INFORMACIÓN CONTACTO
    x_contact_origin = fields.Selection([('odoo', 'Odoo'),('portal', 'Portal')], string='Origen del contacto', tracking=True, default='odoo')
    x_contact_type = fields.Many2many('logyca.contact_types', string='Tipo de contacto', tracking=True, ondelete='restrict')
    x_contact_area = fields.Many2one('logyca.areas', string='Área', tracking=True, ondelete='restrict')
    x_contact_job_title = fields.Many2one('logyca.job_title', string='Cargo', tracking=True, ondelete='restrict', domain="[('area_id', '=', x_contact_area)]")
    x_contact_job_title_historic = fields.Char(string='Cargo histórico', tracking=True)
    x_contact_area_historic = fields.Char(string='Área histórica', tracking=True)

    #INFORMACION FACTURACION ELECTRÓNICA
    x_email_invoice_electronic = fields.Char(string='Correo electrónico para recepción electrónica de facturas', tracking=True)

    #INFORMACIÓN EDUCACIÓN - CLIENTES
    X_is_a_student = fields.Boolean(string='¿Es estudiante?', tracking=True)
    x_educational_institution = fields.Char(string='Institución', tracking=True)
    x_educational_faculty = fields.Char(string='Facultad', tracking=True)
    x_taken_courses_logyca = fields.Boolean(string='¿Ha tomado cursos en LOGYCA?', tracking=True)

    #CAMPOS HISTORICOS
    x_owner_history = fields.Char(string='Propietario historico', tracking=True)
    x_info_creation_history = fields.Char(string='Información de creación y modificación historica', tracking=True)
    x_history_partner_notes = fields.One2many('logyca.history_partner_notes', 'partner_id', string = 'Notas')
    x_history_partner_emails = fields.One2many('logyca.history_partner_emails', 'partner_id', string = 'Emails')
    x_history_partner_opportunity = fields.One2many('logyca.history_partner_opportunity', 'partner_id', string = 'Oportunidades')
    x_history_partner_case = fields.One2many('logyca.history_partner_case', 'partner_id', string = 'Casos')

    @api.depends('x_asset_range')
    def _date_update_asset(self):
        self.x_date_update_asset = fields.Date.today()

    @api.onchange('x_active_for_logyca', 'active')
    def _onchange_active(self):
        if self.x_active_for_logyca:
            self.active = True
        else:
            self.active = False

    @api.depends('x_active_for_logyca', 'active', 'active_logyca')
    def _depends_active(self):
        for partner in self:
            if partner.x_active_for_logyca:
                partner.active = True
                partner.active_logyca = True
            else:
                partner.active = False
                partner.active_logyca = False

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
                self.x_digit_verification = 0

            if partner.vat and partner.l10n_latam_identification_type_id.description == '31' and len(partner.vat) <= len(multiplication_factors):
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
                self.x_digit_verification = 0

    #---------------Search
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('search_by_vat', False):
            if name:
                args = args if args else []
                args.extend(['|', ['name', 'ilike', name], ['vat', 'ilike', name]])
                name = ''
        return super(ResPartner, self).name_search(name=name, args=args, operator=operator, limit=limit)

    #-----------Validaciones
    @api.constrains('vat')
    def _check_vatnumber(self):
        for record in self:
            cant_vat = 0
            cant_vat_archivado = 0
            name_tercer =  ''
            user_create = ''
            if record.vat:
                obj = self.search([('is_company', '=', True),('vat','=',record.vat)])
                if obj:
                    for tercer in obj:
                        cant_vat = cant_vat + 1
                        if tercer.id != record.id:
                            name_tercer = tercer.name
                            user_create = tercer.create_uid.name
                objArchivado = self.search([('is_company', '=', True),('vat','=',record.vat),('active','=',False)])
                if objArchivado:
                    for tercer in objArchivado:
                        cant_vat_archivado = cant_vat_archivado + 1
                        if tercer.id != record.id:
                            name_tercer = tercer.name
                            user_create = tercer.create_uid.name
        if cant_vat > 1:
            raise ValidationError(_('Ya existe un Cliente ('+name_tercer+') con este número de NIT creado por '+user_create+'.'))                
        if cant_vat_archivado > 1:
            raise ValidationError(_('Ya existe un Cliente ('+name_tercer+') con este número de NIT pero se encuentra archivado, fue creado por '+user_create+'.'))                

    @api.onchange('vat')
    def _onchange_vatnumber(self):
        for record in self:
            if record.vat:
                obj = self.search([('x_type_thirdparty','in',[1,3]),('vat','=',record.vat)])
                if obj:
                    raise UserError(_('Ya existe un Cliente con este número de NIT.'))
                objArchivado = self.search([('x_type_thirdparty','in',[1,3]),('vat','=',record.vat),('active','=',False)])
                if objArchivado:
                    raise UserError(_('Ya existe un Cliente con este número de NIT pero se encuentra archivado.'))

    @api.constrains('child_ids')
    def _check_contacttype(self):
        #Tipo de contacto facturación electronica
        cant_contactsFE = 0
        name_contact = ""
        for record in self.child_ids:            
            ls_contacts = record.x_contact_type  
            
            for i in ls_contacts:
                if i.id == 3:
                    cant_contactsFE = cant_contactsFE + 1
                    name_contact = name_contact +" | "+record.name
    
        if cant_contactsFE > 1:
            raise ValidationError(_('Tiene más de un contacto ('+name_contact+') de tipo facturación electrónica, por favor verificar.')) 
        
        #Tipo de contacto representante ante LOGYCA
        cant_contactsRL = 0
        name_contact = ""
        for record in self.child_ids:            
            ls_contacts = record.x_contact_type  
            
            for i in ls_contacts:
                if i.id == 2:
                    cant_contactsRL = cant_contactsRL + 1
                    name_contact = name_contact +" | "+record.name

        if cant_contactsRL > 1:
            raise ValidationError(_('Tiene más de un contacto ('+name_contact+') como Representante ante LOGYCA, por favor verificar.'))
                
    @api.constrains('x_tax_responsibilities')
    def _check_tax_responsibilities(self):
        #Responsabilidades Tributarias Validas para FE
        if self.company_type == 'company':
            cant_RT = 0
            for record in self.x_tax_responsibilities:   
                if record.valid_for_fe == True:
                    cant_RT = cant_RT + 1

            if cant_RT == 0:
                    raise ValidationError(_('El cliente debe tener una Responsabilidad Tributaria válida para Facturación Electrónica.'))  

    @api.model
    def _run_vat_test(self, vat_number, default_country, partner_is_company=True):
        # OVERRIDE account
        check_result = None
        return check_result
