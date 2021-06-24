# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RVCBeneficiary(models.Model):
    _name = 'rvc.beneficiary'
    _description = 'RVC Beneficiary'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Patrocinado')
    vat = fields.Char('Número de documento')
    phone = fields.Char('Phone', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    date_send = fields.Date(string='Fecha de Envio')
    x_company_size = fields.Selection([('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')], string='Tamaño empresa', related='partner_id.x_company_size', readonly=True, store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name_contact = fields.Char('Nombre del contacto')
    phone_contact = fields.Char('Phone',)
    email_contact = fields.Char('Email')
    cargo_contact = fields.Char('Cargo')
    active = fields.Boolean('Activo', default=True)
    cant_cod = fields.Integer('Cantidad de Códigos')
    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector', related='partner_id.macro_sector')



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