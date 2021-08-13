# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class RVCSponsored(models.Model):
    _name = 'rvc.sponsored'
    _description = 'RVC Sponsored'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Patrocinador')
    vat = fields.Char('NIT', related='partner_id.vat')
    phone = fields.Char('Phone', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    x_company_size = fields.Selection([('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')], string='Tamaño empresa', related='partner_id.x_company_size', readonly=True, store=True)
    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector', related='partner_id.macro_sector')       

    contact_name = fields.Char('Nombre del contacto')
    contact_phone = fields.Char('Phone',)
    contact_email = fields.Char('Email')
    contact_position = fields.Char('Cargo')
    active = fields.Boolean('Activo', default=True)


    _sql_constraints = [
        ('partner_id_company_uniq', 'unique (vat,company_id)', 'La empresa halonadora ya esta creada')
    ]    

    def name_get(self):
        return [(sponsored.id, '%s - %s' % (sponsored.partner_id.name, sponsored.vat)) for sponsored in self]

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        #es un contacto
        if self.partner_id.is_company == False or self.partner_id.parent_id:
            self.clear_contact_fields()

            partner = self.partner_id

            self.contact_name = partner.name
            self.contact_phone = partner.phone if partner.phone else partner.mobile
            self.contact_email = partner.email
            self.contact_position = partner.x_contact_job_title.name if partner.x_contact_job_title else ''
    
    def clear_contact_fields(self):
        self.contact_name = ""
        self.contact_phone = ""
        self.contact_email = ""
        self.contact_position = ""

    @api.model
    def create(self, vals):
        partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
        if partner_id:
            if partner_id.active == False:
                raise ValidationError('¡Error de validación! La empresa NO está activa.')
            if partner_id.x_type_vinculation:
                    for vinculation in partner_id.x_type_vinculation:
                        if vinculation.code == '01':
                            raise ValidationError('¡Error de validación! La empresa es miembro.')
        return super(RVCSponsored, self).create(vals)


    def write(self, vals):
        partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
        if partner_id:
            if partner_id.active == False:
                raise ValidationError('¡Error de validación! La empresa NO está activa.')
            if partner_id.x_type_vinculation:
                    for vinculation in partner_id.x_type_vinculation:
                        if vinculation.code == '01':
                            raise ValidationError('¡Error de validación! La empresa es miembro.')
        return super(RVCSponsored, self).write(vals)

                
    def deactivate_beneficiary(self):
        for rec in self:
            rec.active = False

    def activate_beneficiary(self):
        for rec in self:
            rec.active = True
