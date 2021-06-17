# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class RVCSponsored(models.Model):
    _name = 'rvc.sponsored'
    _description = 'RVC Sponsored'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Patrocinador')
    vat = fields.Char('Número de documento', related='partner_id.vat')
    name_contact = fields.Char('Nombre del contacto')
    phone = fields.Char('Phone', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    state = fields.Selection([('draft', 'Draft'), 
                                ('confirm', 'Confirm')], string='state', readonly=True, default='draft')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    x_company_size = fields.Selection([('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')], string='Tamaño empresa', related='partner_id.x_company_size', readonly=True, store=True)                                


    def action_confirm(self):
        self.write({'state': 'confirm'})

#