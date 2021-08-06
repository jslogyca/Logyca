# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class RVCSponsored(models.Model):
    _name = 'rvc.sponsored'
    _description = 'RVC Sponsored'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Patrocinador')
    vat = fields.Char('NIT')
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
            if partner_id and not partner_id.x_type_vinculation.code in ('01'):
                raise ValidationError('La empresa No es Miembro')
        return super(RVCSponsored, self).create(vals)


    def write(self, vals):
        if vals.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id','=',vals.get('partner_id', False))])
            if partner_id and not partner_id.active:
                raise ValidationError('La empresa esta activa')
            if partner_id and not partner_id.x_type_vinculation.code in ('01'):
                raise ValidationError('La empresa No es Miembro')
        return super(RVCSponsored, self).write(vals)

                

#