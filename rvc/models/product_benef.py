# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class ProductBenef(models.Model):
    _name = 'product.benef'
    _description = 'Product Benef'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    state = fields.Selection([('draft', 'Draft'), 
                                    ('notified', 'Notified'),
                                    ('confirm', 'Confirm'),
                                    ('rejected', 'Rejected'),
                                    ('cancel', 'Cancel'),
                                    ('done', 'Done')], string='State', default='draft', readonly=True, track_visibility='onchange')
    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria', track_visibility='onchange')
    parent_id = fields.Many2one('rvc.sponsored', string='Empresa Patrocinadora', track_visibility='onchange')
    product_id = fields.Many2one('product.rvc', string='Producto', track_visibility='onchange')
    agreement_id = fields.Many2one('agreement.rvc', string='Agreement', track_visibility='onchange')
    name = fields.Char(string='Name', track_visibility='onchange')
    cant_cod = fields.Float('Cantidad de Códigos', track_visibility='onchange')
    cant_cod_disp = fields.Float('Cantidad de Códigos Disponibles', track_visibility='onchange')
    type_beneficio = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], related='product_id.type_beneficio', readonly=True, store=True, string="Beneficio", track_visibility='onchange')
    sub_product_ids = fields.Many2one('sub.product.rvc', string='Sub-Productos', track_visibility='onchange')
    date_end = fields.Date(string='Date End', track_visibility='onchange')
    gln = fields.Char('GLN', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company, track_visibility='onchange')
    name_contact = fields.Char('Nombre del contacto', related='partner_id.name_contact', track_visibility='onchange')
    phone_contact = fields.Char('Phone', related='partner_id.phone_contact', track_visibility='onchange')
    email_contact = fields.Char('Email', related='partner_id.email_contact', track_visibility='onchange')
    cargo_contact = fields.Char('Cargo', related='partner_id.cargo_contact', track_visibility='onchange')
    vat = fields.Char('Número de documento', related='partner_id.vat', track_visibility='onchange')

    def unlink(self):
        for product_benef in self:
            if product_benef.state not in ('draft', 'cancel'):
                raise ValidationError(_('You cannot delete an Benef which is not draft or cancelled. You should create a credit note instead.'))
        return super(ProductBenef, self).unlink()


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_confirm(self):
        self.write({'state': 'confirm'})


    def action_done(self):
        self.write({'state': 'done'})


    def action_rejected(self):
        self.write({'state': 'rejected'})


    def action_re_done(self):
        self.write({'state': 'confirm'})


    def action_notified(self):
        for product_benef in self:
            if product_benef.state in ('draft'):
                view_id = self.env.ref('rvc.rvc_template_email_wizard_form').id,
                return {
                    'name':_("Are you sure?"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'rvc.template.email.wizard',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]'
                }
        self.write({'state': 'notified'})

#
