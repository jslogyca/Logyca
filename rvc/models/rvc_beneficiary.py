# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class RVCBeneficiary(models.Model):
    _name = 'rvc.beneficiary'
    _description = 'RVC Beneficiary'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    partner_id = fields.Many2one('res.partner', string='Patrocinado')
    vat = fields.Char('Número de documento', related='partner_id.vat')
    parent_id = fields.Many2one('res.partner', string='Patrocinador')
    product_id = fields.Many2one('product.product', string='Beneficio')
    x_sector_id = fields.Many2one('logyca.sectors', string='Sector', related='partner_id.x_sector_id', readonly=True, store=True)
    date_send = fields.Date(string='Fecha de Envio')
    state = fields.Selection([('draft', 'Draft'), 
                                ('confirm', 'Confirm'),
                                ('send', 'Send'),
                                ('done', 'Entregado')], string='state', readonly=True, default='draft')
    x_company_size = fields.Selection([('1', 'Mipyme'),
                                        ('2', 'Pyme'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande'),
                                        ('5', 'Micro'),
                                        ('6', 'Pequeña')], string='Tamaño empresa', related='partner_id.x_company_size', readonly=True, store=True)
    type_beneficio = fields.Selection([('codigos', 'Identificación de Productos'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], string="Beneficio")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    name_contact = fields.Char('Nombre del contacto')
    phone = fields.Char('Phone', related='partner_id.phone')
    email = fields.Char('Email', related='partner_id.email')
    cant_cod = fields.Integer('Cantidad de Códigos')


    def action_confirm(self):
        self.write({'state': 'confirm'})


    def action_send(self):
        self.write({'state': 'send'})
    
    

#