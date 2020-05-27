# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import requests
import datetime

#---------------------------Modelo ACCOUNT-MOVE/ MOVIMIENTO DETALLE-------------------------------#

# Encabezado Movimiento
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.model
    def _get_default_country_id(self):
        country_id = 49
        
        if self.partner_id:
            partner = self.env['res.partner'].browse(self.partner_id.id)
            country_id = partner.country_id
        
        values = {
                'x_country_account_id': country_id ,                
            }
        self.update(values)
        
        return country_id
    
    #PAÍS 
    x_country_account_id = fields.Many2one('res.country', string='País', default=_get_default_country_id, track_visibility='onchange')
    #NUMERO DE ORDEN DE COMPRA
    x_num_order_purchase = fields.Char(string='Número orden de compra', track_visibility='onchange')
    #FACTURACIÓN ELECTRONICA
    x_date_send_dian = fields.Datetime(string='Fecha de envío a la DIAN', copy=False)
    x_send_dian = fields.Boolean(string='Enviado a la DIAN', copy=False)
    x_cufe_dian = fields.Char(string='CUFE - Código único de facturación electrónica', copy=False)
    x_motive_error = fields.Text(string='Motivo de error', copy=False)
    
    @api.depends('partner_id')
    @api.onchange('partner_id')
    def _onchange_partner_id_country(self):
        
        partner = self.env['res.partner'].browse(self.partner_id.id)
        
        values = {
                'x_country_account_id': partner.country_id ,                
            }
        self.update(values)
    
    #Purchase - Se reemplaza metodo propio de odoo por el nuestro
    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        ''' Load from either an old purchase order, either an old vendor bill.

        When setting a 'purchase.bill.union' in 'purchase_vendor_bill_id':
        * If it's a vendor bill, 'invoice_vendor_bill_id' is set and the loading is done by '_onchange_invoice_vendor_bill'.
        * If it's a purchase order, 'purchase_id' is set and this method will load lines.

        /!\ All this not-stored fields must be empty at the end of this function.
        '''
        if self.purchase_vendor_bill_id.vendor_bill_id:
            self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id:
            return

        # Copy partner.
        self.partner_id = self.purchase_id.partner_id
        self.x_country_account_id = self.purchase_id.partner_id.country_id.id
        self.fiscal_position_id = self.purchase_id.fiscal_position_id
        self.invoice_payment_term_id = self.purchase_id.payment_term_id
        self.currency_id = self.purchase_id.currency_id

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            prepare_line = line._prepare_account_move_line(self)
            if line.x_budget_group:
                prepare_line['x_budget_group'] = line.x_budget_group
            else:
                raise ValidationError(_('El grupo presupuestal esta vacio, por favor verificar.'))     
            new_line = new_lines.new(prepare_line)
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line
        new_lines._onchange_mark_recompute_taxes()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = set(self.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
        refs = [ref for ref in refs if ref]
        self.ref = ','.join(refs)

        # Compute _invoice_payment_ref.
        if len(refs) == 1:
            self._invoice_payment_ref = refs[0]

        self.purchase_id = False
        self._onchange_currency()
        self.invoice_partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]
    
    #Validaciones antes de permitir PUBLICAR una factura
    def action_post(self): 
        
        #Validar que las cuentas de resultado 4-5-6 OBLIGUEN a cuentas analítica o etiqueta analítica
        for invoice_line in self.invoice_line_ids:            
            if str(invoice_line.account_id.code).find("4", 0, 1) != -1 or str(invoice_line.account_id.code).find("5", 0, 1) != -1 or str(invoice_line.account_id.code).find("6", 0, 1) != -1:
                if not invoice_line.analytic_account_id and not invoice_line.analytic_tag_ids:
                    raise ValidationError(_("No se digito información analítica (Cuenta o Etiqueta) para el registro "+invoice_line.name+", por favor verificar."))
                
        for line in self.line_ids:
            if str(line.account_id.code).find("4", 0, 1) != -1 or str(line.account_id.code).find("5", 0, 1) != -1 or str(line.account_id.code).find("6", 0, 1) != -1:
                if not line.analytic_account_id and not line.analytic_tag_ids:
                    raise ValidationError(_("No se digito información analítica (Cuenta o Etiqueta) para el registro "+line.name+", por favor verificar."))
        
        #Contacto de facturación electronica        
        cant_contactsFE = 0
        if self.type == 'out_invoice' or self.type == 'out_refund' or self.type == 'out_receipt':
            
            #Fecha de factura
            if (self.date != fields.Date.context_today(self)) and (self.invoice_date != fields.Date.context_today(self)):
                #https://poncesoft.blogspot.com/2017/07/consulta-de-fecha-actual-traves-de-la.html - LINK DE APOYO
                raise ValidationError(_('La fecha de la factura no puede ser diferente a la fecha actual, por favor verificar.'))     
            
            for line in self.invoice_line_ids:
                if not line.analytic_account_id:
                    raise ValidationError(_('La cuenta analitica esta vacia para el registro '+line.name+', por favor verificar.'))     
            
            if self.partner_id.parent_id:
                partner = self.env['res.partner'].browse(self.partner_id.parent_id.id)
            else:
                partner = self.env['res.partner'].browse(self.partner_id.id)
                
            for record in partner.child_ids:   
                ls_contacts = record.x_contact_type              
                for i in ls_contacts:
                    if i.id == 3:
                        cant_contactsFE = cant_contactsFE + 1
                        if not record.name:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene nombre, por favor verificar.'))     
                        if record.x_active_for_logyca == False:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no esta activo, por favor verificar.'))    
                        if not record.street:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene dirección, por favor verificar.'))    
                        if not record.x_city:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene ciudad, por favor verificar.'))    
                        if not record.email:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene email, por favor verificar.'))    
                        if not record.phone and not record.mobile:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene teléfono, por favor verificar.'))
                        
            if cant_contactsFE == 0:
                raise ValidationError(_('El cliente al que pertenece la factura no tiene un contacto de tipo facturación electrónica, por favor verificar.'))     
        
        return super(AccountMove, self).action_post()

# Nota credito
class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"
    
    refund_method = fields.Selection(default='cancel')
    
    reason = fields.Selection([('1', 'Devolución de servicio'),
                              ('2', 'Diferencia del precio real y el importe cobrado'),
                              ('3', 'Se emitió una factura por error de tercero')], string='Motivo', required=True)
        
# Detalle Movimiento
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal', index=True, ondelete='restrict')
    
    #Cuenta analitica 
    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        if self.analytic_account_id:
            self.analytic_tag_ids = [(5,0,0)]
            
    #Etiqueta analitica
    @api.onchange('analytic_tag_ids')
    def _onchange_analytic_tag_ids(self):
        if self.analytic_tag_ids:
            self.analytic_account_id = False
            
    
        
    

