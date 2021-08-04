# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import json
import logging

_logger = logging.getLogger(__name__)

class ProductBenef(models.Model):
    _name = 'product.benef'
    _description = 'Product Benef'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    state = fields.Selection([('draft', 'Draft'), 
                                    ('notified', 'Notificado'),
                                    ('confirm', 'Aceptado'),
                                    ('rejected', 'Rechazado'),
                                    ('cancel', 'Cancelado'),
                                    ('done', 'Entregado')], string='State', default='draft', readonly=True, track_visibility='onchange')
    partner_id = fields.Many2one('rvc.beneficiary', string='Empresa Beneficiaria', track_visibility='onchange')
    parent_id = fields.Many2one('rvc.sponsored', string='Empresa Patrocinadora', track_visibility='onchange')
    product_id = fields.Many2one('product.rvc', string='Producto', track_visibility='onchange')
    agreement_id = fields.Many2one('agreement.rvc', string='Agreement', track_visibility='onchange')
    name = fields.Char(string='Name', track_visibility='onchange')
    cant_cod = fields.Float('Cantidad de Códigos', track_visibility='onchange')
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


    def name_get(self):
        return [(product.id, '%s - %s' % (product.partner_id.partner_id.name, product.product_id.name)) for product in self]    

    def unlink(self):
        for product_benef in self:
            if product_benef.state not in ('draft', 'cancel'):
                raise ValidationError(_('You cannot delete an Benef which is not draft or cancelled. You should create a credit note instead.'))
        return super(ProductBenef, self).unlink()


    def action_cancel(self):
        self.write({'state': 'cancel'})


    def action_confirm(self):
        for product_benef in self:
            if product_benef.state in ('notified'):
                view_id = self.env.ref('rvc.rvc_template_email_confirm_wizard_form').id,
                return {
                    'name':_("Enviar Aceptación"),
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'rvc.template.email.wizard',
                    'type': 'ir.actions.act_window',
                    'nodestroy': True,
                    'target': 'new',
                    'domain': '[]'
                }
        self.write({'state': 'confirm'})


    def action_done(self):
        for product_benef in self:
            if product_benef.state in ('confirm'):
                if self._validate_gln() and self._validate_bought_products():
                    view_id = self.env.ref('rvc.rvc_template_email_done_wizard_form').id,
                    return {
                        'name':_("Enviar Kit de Bienvenida"),
                        'view_mode': 'form',
                        'view_id': view_id,
                        'view_type': 'form',
                        'res_model': 'rvc.template.email.wizard',
                        'type': 'ir.actions.act_window',
                        'nodestroy': True,
                        'target': 'new',
                        'domain': '[]'
                    }
        self.write({'state': 'done'})


    def action_rejected(self):
        for product_benef in self:
            view_id = self.env.ref('rvc.rvc_template_email_rejected_wizard_form').id,
            return {
                'name':_("Rechazar Beneficio"),
                'view_mode': 'form',
                'view_id': view_id,
                'view_type': 'form',
                'res_model': 'rvc.template.email.wizard',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'new',
                'domain': '[]'
            }
        self.write({'state': 'rejected'})


    def action_re_done(self):
        self.write({'state': 'confirm'})


    def action_notified(self):
        for product_benef in self:
            if product_benef.state in ('draft', 'notified'):
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
        
    @api.model
    def create(self, vals):
        res = super(ProductBenef, self).create(vals)
        res._validate_gln()
        res._validate_bought_products()
        return res

    
    def write(self, vals):
        res = super(ProductBenef, self).write(vals)
        self._validate_gln()
        self._validate_bought_products()
        return res

    
    def _validate_gln(self, strict_validation=False):
        available_gln_codes = ""
        found = False
        
        if self.partner_id and (self.product_id.type_beneficio == 'codigos' or self.product_id.type_beneficio == 'colabora'):
            
            import requests
            url = "https://asctestdocker.azurewebsites.net/codes/EmpresaGln/"
            payload = {'nit': str(self.vat)}

            response = requests.get(url, data=json.dumps(payload))
            if response.status_code == 200:
                result = response.json()
                
                #cuando no escriben un gln pero se encontró que hay uno registrado.
                if len(result) == 1 and not self.gln:
                    self.gln = result[0].get('id')
                    return True

                for gln in result:
                    available_gln_codes = available_gln_codes + "\n" + str(gln.get('id'))

                    #cuando escriben un gln lo buscamos entre los que hay registrados para el nit dado.
                    if str(gln.get('id')) == self.gln: 
                        found = True

            if not found and available_gln_codes:
                raise ValidationError('\
                    La empresa seleccionada tiene más de un GLN disponible, utilice alguno de los siguientes: \n %s' % str(available_gln_codes))
            elif strict_validation and not found and not available_gln_codes:
                raise ValidationError('No hay códigos GLN activos para la empresa seleccionada .')
                
    def _validate_bought_products(self):
        import requests
        #url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str("10203040"))
        url = "https://asctestdocker.azurewebsites.net/codes/CodigosByEmpresa/?Nit=%s&EsPesoVariable=False&TraerCodigosReservados=True" % (str(self.vat))
        
        
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            
            if result.get('CodigosCompradosDisponibles') > 0:
                 raise ValidationError(\
                    '¡Lo sentimos! La empresa seleccionada tiene %s código(s) comprados disponibles.' % (str(result.get('CodigosCompradosDisponibles'))) )
        return True
