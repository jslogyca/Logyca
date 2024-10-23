# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
import logging

class RVCBeneficiary(models.Model):
    _name = 'rvc.beneficiary'
    _description = 'RVC Beneficiary'
    _inherit = 'mail.thread'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Patrocinado')
    contact_id = fields.Many2one('res.partner', string='Contacto')
    vat = fields.Char('Número de documento', related='partner_id.vat')
    phone = fields.Char('Teléfono', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id')
    date_send = fields.Date(string='Fecha de Envio', tracking=True)
    x_company_size = fields.Selection(string='Tamaño empresa', related='partner_id.x_company_size')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, tracking=True)
    contact_name = fields.Char('Nombre Contacto', tracking=True)
    contact_phone = fields.Char('Teléfono Contacto', tracking=True)
    contact_email = fields.Char('Email Contacto', tracking=True)
    contact_position = fields.Char('Cargo Contacto', tracking=True)
    active = fields.Boolean('Activo', default=True, tracking=True)
    codes_quantity = fields.Integer('Cantidad de Códigos', tracking=True)
    macro_sector = fields.Selection(string='Macrosector', related='partner_id.macro_sector')

    _sql_constraints = [
        ('rvc_beneficiary_uniq', 'unique (partner_id)', 'La empresa beneficiaria que está tratando de crear ya existe.')
    ]

    def name_get(self):
        return [(benef.id, '%s - %s' % (benef.vat, benef.partner_id.name)) for benef in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|', ['vat', 'like', name], ['partner_id', operator, name], ['email', operator, name], ['contact_email', operator, name]]
        rvc_beneficiary_union_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return self.browse(rvc_beneficiary_union_ids).name_get()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.contact_id = False

    @api.onchange('contact_id')
    def onchange_contact_id(self):
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
        if vals.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
            if partner_id:
                if partner_id.active == False:
                    raise ValidationError('¡Error de validación! La empresa NO está activa.')
        return super(RVCBeneficiary, self).create(vals)

    def write(self, vals):
        if vals.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
            if partner_id:
                if partner_id.active == False:
                    raise ValidationError('¡Error de validación! La empresa NO está activa.')
                if partner_id.x_type_vinculation:
                    for vinculation in partner_id.x_type_vinculation:
                        if vinculation.code == '01':
                            raise ValidationError('¡Error de validación! La empresa es miembro.')
        return super(RVCBeneficiary, self).write(vals)

    def deactivate_beneficiary(self):
        for rec in self:
            rec.active = False

    def activate_beneficiary(self):
        for rec in self:
            rec.active = True
