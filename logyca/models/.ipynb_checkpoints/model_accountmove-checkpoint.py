# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
import requests
import datetime
import base64

import logging
_logger = logging.getLogger(__name__)
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
    #Tiene Nota Credito
    x_have_out_invoice = fields.Boolean(string='Tiene NC', compute='_have_nc')    
    
    def _have_nc(self):
        query_fac = '''
            select a.id,a.name,b.id,b.name
            from account_move a
            inner join account_move b on a.id = b.reversed_entry_id and b.state = 'posted'
            where a.id = %s
        ''' % (self.id)
        
        self._cr.execute(query_fac)
        result_query_fac = self._cr.dictfetchall()
        
        query_nc = '''
            select id,name 
            from account_move 
            where id = %s and state = 'posted' and reversed_entry_id is not null
        ''' % (self.id)
        
        self._cr.execute(query_nc)
        result_query_nc = self._cr.dictfetchall()
            
        if result_query_fac or result_query_nc:
            #raise ValidationError(_('TIENE NC'))    
            self.x_have_out_invoice = True
        else:
            #raise ValidationError(_('NO TIENE NC'))    
            self.x_have_out_invoice = False
        
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
        
        
        cant_contactsFE = 0
        #cant_RT = 0
        if self.type == 'out_invoice' or self.type == 'out_refund' or self.type == 'out_receipt':            
            # Referencia
            if not self.ref:
                raise ValidationError(_('No se dígito información para el campo Referencia, por favor verificar.'))     
            #Número orden de compra
            if not self.x_num_order_purchase:
                raise ValidationError(_('No se dígito información para el campo Número orden de compra, por favor verificar.'))     
            #Plazos de pago
            if not self.invoice_payment_term_id:
                raise ValidationError(_('No se dígito información para el campo Plazos de pago, por favor verificar.'))                 
            
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
               
            #Responsabilidades tributarias            
            #for partner_responsibilities in partner.x_tax_responsibilities:   
            #    if partner_responsibilities.valid_for_fe == True:
            #        cant_RT = cant_RT + 1

            #if cant_RT == 0:
            #        raise ValidationError(_('El cliente debe tener una Responsabilidad Tributaria válida para Facturación Electrónica.'))  
                        
            #Contacto de facturación electronica        
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
    description = fields.Text(string='Descripción')
    
    
    def reverse_moves(self):
        self.refund_method = 'cancel'
        #Validar que no deje crear NC a facturas ya pagadas
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id        
        for move in moves:
            if move.invoice_payment_state == 'paid':
                    raise ValidationError(_('La factura '+move.name+' ya esta pagada no se puede hacer nota crédito.'))
        #Ejecutar metodo original
        return super(AccountMoveReversal, self).reverse_moves()
        
# Detalle Movimiento
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal', index=True, ondelete='restrict')
    # Fields Reports
    #x_vat_partner = fields.Char(string='NIT Asociado', store=True, readonly=True, related='partner_id.vat', change_default=True)
    x_type_doc_partner = fields.Char(string='NIT Asociado', store=True, readonly=True, related='partner_id.vat')
    x_account_analytic_group = fields.Many2one(string='Grupo Analítico / Familia', store=True, readonly=True, related='analytic_account_id.group_id', change_default=True)
    x_account_analytic_group_two = fields.Many2one(string='Grupo Analítico / Línea', store=True, readonly=True, related='x_account_analytic_group.parent_id', change_default=True)
    #x_analytic_line_account = fields.Many2one(string='Cuenta Analítica Calculada', store=True, readonly=True, related='analytic_line_ids.account_id', change_default=True)
    #x_account_analytic_group = fields.Many2one(string='Grupo Analítico / Familia', store=True, readonly=True, related='analytic_line_ids.group_id', change_default=True)
    #x_account_analytic_group_two = fields.Many2one(string='Grupo Analítico / Línea', store=True, readonly=True, related='x_account_analytic_group.parent_id', change_default=True)
    
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
            
# Reportes Contabilidad
class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    
    #NIT del asociado
    x_vat = fields.Char(string='NIT Asociado', store=True, readonly=True)
    #Grupo Analitico
    x_account_analytic_group = fields.Many2one('account.analytic.group', string='Grupo Analítico / Familia', readonly=True)
    x_account_analytic_group_two = fields.Many2one('account.analytic.group', string='Grupo Analítico / Línea', readonly=True)
    #Categoria de producto
    product_categ_id_fam = fields.Many2one('product.category', string='Categoría de Prodcuto / Familia', readonly=True)
    product_categ_id_lin = fields.Many2one('product.category', string='Categoría de Prodcuto / Línea', readonly=True)
        
    def _select(self):
        add_select = '''
            , partner.vat as x_vat, 
            analytic.group_id as x_account_analytic_group, 
            analytic_group.parent_id as x_account_analytic_group_two,
            category_fam.id as product_categ_id_fam,
            category_lin.id as product_categ_id_lin            
        '''
        return super(AccountInvoiceReport, self)._select() + add_select
    
    def _from(self):
        add_from = '''
            LEFT JOIN account_analytic_account analytic ON line.analytic_account_id = analytic.id 
            LEFT JOIN account_analytic_group analytic_group ON analytic.group_id = analytic_group.id
            LEFT JOIN product_category category_subfam ON template.categ_id = category_subfam.id
            LEFT JOIN product_category category_fam ON category_subfam.parent_id = category_fam.id
            LEFT JOIN product_category category_lin ON category_fam.parent_id = category_lin.id
        '''
        
        return super(AccountInvoiceReport, self)._from() + add_from
    
    def _group_by(self):
        add_group = '''
            , partner.vat,analytic.group_id,analytic_group.parent_id,category_fam.id,category_lin.id
        '''
        return super(AccountInvoiceReport, self)._group_by() + add_group
    
#Lineas Analiticas
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    x_groupline_id = fields.Many2one(string='Grupo Analítico / Línea', store=True, readonly=True, related='group_id.parent_id', change_default=True)    

#Pagos
class AccountPayment(models.Model):
    _inherit = 'account.payment'
    x_payment_file = fields.Boolean(string='Reportado en archivo de pago')    

#Importar Bancos CSV
class AccountBankStatementImport(models.TransientModel):
    _inherit = 'account.bank.statement.import'
    
    #attachment_ids = fields.Many2many('ir.attachment', string='Files', required=True, help='Get you bank statements in electronic format from your bank and select them here.')
    x_documents_odoo = fields.Many2one('documents.document', string='Documentos en Odoo', ondelete='restrict')
    
    def import_file(self):        
        if self.x_documents_odoo:            
            for data_file in self.x_documents_odoo:                 
                self.attachment_ids = data_file.attachment_id
            return super(AccountBankStatementImport, self).import_file()              
        else:
            return super(AccountBankStatementImport, self).import_file()
        
#Ingresos diferidos
class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    move_ids = fields.Many2one(related='original_move_line_ids.move_id', string='Movimiento Original', readonly=True, copy=False)
        