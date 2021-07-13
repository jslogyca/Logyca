# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RVCBeneficiary(models.Model):
    _name = 'rvc.beneficiary'
    _description = 'RVC Beneficiary'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Name', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Patrocinado', track_visibility='onchange')
    vat = fields.Char('Número de documento', track_visibility='onchange')
    phone = fields.Char('Phone', related='partner_id.phone', track_visibility='onchange')
    email = fields.Char('Email', related='partner_id.email', track_visibility='onchange')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    date_send = fields.Date(string='Fecha de Envio', track_visibility='onchange')
    x_company_size = fields.Selection([('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')], string='Tamaño empresa', related='partner_id.x_company_size', readonly=True, store=True, track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, track_visibility='onchange')
    name_contact = fields.Char('Nombre del contacto', track_visibility='onchange')
    phone_contact = fields.Char('Phone', track_visibility='onchange')
    email_contact = fields.Char('Email', track_visibility='onchange')
    cargo_contact = fields.Char('Cargo', track_visibility='onchange')
    active = fields.Boolean('Activo', default=True, track_visibility='onchange')
    cant_cod = fields.Integer('Cantidad de Códigos', track_visibility='onchange')
    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector', related='partner_id.macro_sector', track_visibility='onchange')



    @api.onchange('vat')
    def _onchange_vat(self):
        if self.vat:
            partner_id = self.env['res.partner'].search([('vat','=',self.vat), ('is_company','=',True)])
            if partner_id:
                self.write({'partner_id': partner_id.id})
            else:
                raise ValidationError('La empresa no esta registrada en Odoo')


    @api.model
    def create(self, vals):
        if vals.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
            if partner_id and not partner_id.active:
                raise ValidationError('La empresa esta activa')
            if partner_id and partner_id.x_type_vinculation.code in ('01'):
                raise ValidationError('La empresa es Miembro')
        return super(RVCBeneficiary, self).create(vals)


    def write(self, vals):
        if vals.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
            if partner_id and not partner_id.active:
                raise ValidationError('La empresa esta activa')
            if partner_id and partner_id.x_type_vinculation.code in ('01'):
                raise ValidationError('La empresa es Miembro')
        return super(RVCBeneficiary, self).write(vals)

    
    

#