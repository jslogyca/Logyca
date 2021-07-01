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
                                    ('done', 'Done')], string='State', default='draft', readonly=True)
    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria')
    parent_id = fields.Many2one('rvc.sponsored', string='Empresa Patrocinadora')
    product_id = fields.Many2one('product.rvc', string='Producto')
    agreement_id = fields.Many2one('agreement.rvc', string='Agreement')
    name = fields.Char(string='Name')
    cant_cod = fields.Integer('Cantidad de Códigos')
    cant_cod_disp = fields.Integer('Cantidad de Códigos Disponibles')
    type_beneficio = fields.Selection([('codigos', 'Derechos de Identificación'), 
                                    ('colabora', 'Colabora'),
                                    ('analitica', 'Analítica')], related='product_id.type_beneficio', readonly=True, store=True, string="Beneficio")
    sub_product_ids = fields.Many2one('sub.product.rvc', string='Sub-Productos')
    date_end = fields.Date(string='Date End')
    gln = fields.Char('GLN')
    

    def unlink(self):
        for product_benef in self:
            if product_benef.state not in ('draft', 'cancel'):
                raise ValidationError(_('You cannot delete an Benef which is not draft or cancelled. You should create a credit note instead.'))
        return super(ProductBenef, self).unlink()


    def action_notified(self):
        self.write({'state': 'notified'})


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

#
