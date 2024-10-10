# -*- coding: utf-8 -*-

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class RVCSponsored(models.Model):
    _name = 'rvc.sponsor'
    _description = 'RVC Sponsor'
    _rec_name = 'partner_id'

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Patrocinador')
    name = fields.Char('Nombre', related='partner_id.name', store=True)
    vat = fields.Char('NIT', related='partner_id.vat', store=True)
    phone = fields.Char('Teléfono', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    x_company_size = fields.Selection(string='Tamaño empresa', related='partner_id.x_company_size')
    macro_sector = fields.Selection(string='Macrosector', related='partner_id.macro_sector')       

    contact_name = fields.Char('Nombre Contacto')
    contact_phone = fields.Char('Teléfono Contacto',)
    contact_email = fields.Char('Email Contacto')
    contact_position = fields.Char('Cargo Contacto')
    active = fields.Boolean('Activo', default=True)


    _sql_constraints = [
        ('partner_id_company_uniq', 'unique (vat,company_id)', 'La empresa halonadora ya esta creada')
    ]

    #se usa para ocultar los campos técnicos de los filtros y agrupaciones
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(RVCSponsored, self).fields_get(allfields, attributes)
        fields_to_hide = ['vat']
        for field in fields_to_hide:
            res[field]['selectable'] = False  # disable field visible in filter
            res[field]['sortable'] = False  # disable field visible in grouping
        return res

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
        return super(RVCSponsored, self).create(vals)


    def write(self, vals):
        partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
        if partner_id:
            if partner_id.active == False:
                raise ValidationError('¡Error de validación! La empresa NO está activa.')
        return super(RVCSponsored, self).write(vals)

                
    def deactivate_beneficiary(self):
        for rec in self:
            rec.active = False

    def activate_beneficiary(self):
        for rec in self:
            rec.active = True
