# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
import requests
import datetime
import base64
import json

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
    x_country_account_id = fields.Many2one('res.country', string='País', default=_get_default_country_id, tracking=True)
    #NUMERO DE ORDEN DE COMPRA
    x_num_order_purchase = fields.Char(string='Número orden de compra', tracking=True)
    #FACTURACIÓN ELECTRONICA
    x_date_send_dian = fields.Datetime(string='Fecha de envío a la DIAN', copy=False)
    x_send_dian = fields.Boolean(string='Enviado a la DIAN', copy=False)
    x_cufe_dian = fields.Char(string='CUFE - Código único de facturación electrónica', copy=False)
    x_motive_error = fields.Text(string='Motivo de error', copy=False)
    x_status_dian = fields.Char(string='Estado en la DIAN', copy=False)
    #Tiene Nota Credito
    x_have_out_invoice = fields.Boolean(string='Tiene NC', compute='_have_nc')    
    #Tiene Aprobaciones
    x_have_approval_request = fields.Boolean(string='Tiene Aprobaciones', compute='_have_approval_request')    
    x_create_approval_request = fields.Boolean(string='Crearon Aprobación para NC',store = True, tracking=True)    
    x_approved_approval_request = fields.Boolean(string='Aprobaron la creación de la NC',store = True, tracking=True)   
    #Es factura de facturación masiva
    x_is_mass_billing = fields.Boolean(string='Factura creada por el proceso de facturación masiva.')
    #Valor total descuentos
    x_value_discounts = fields.Monetary(string='Valor descuentos', default=0.0, currency_field='company_currency_id')
    x_discounts_deadline = fields.Date(string='Fecha límite descuento condicionado')    
    x_amount_total_discounts = fields.Monetary(string='Total con descuentos', default=0.0, currency_field='company_currency_id', compute='_compute_amount_total_discounts')
    x_discount_payment = fields.Boolean(string='Pago con descuento', copy=False)
    #Recibo de pago - Campo temporal
    x_receipt_payment = fields.Char(string='N° Recibo de pago', copy=False)
    x_journal_resolution_num = fields.Char(string='Number', related='journal_id.x_resolution_number')

    @api.onchange('state')
    def _compute_x_status_dian(self):
        if self.state == 'posted' and self.x_cufe_dian:
            self._get_status_dian()
            self._get_url_invoice_dian(self.x_cufe_dian)

    def get_status_dian(self):
        token = self._get_token()
        if token:
            status_dian = self._get_status_dian_by_cufe(token, self.x_cufe_dian)
            if status_dian:
                self._update_status_dian(self, status_dian)
    
    def get_url_invoice_dian(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.x_cufe_dian,
            'target': 'new',
        }


    def _get_token(self) -> str:
        url = "https://api-factura-electronica-co.saphety.com/v2/auth/gettoken"

        payload = {
            "username": 'ktoscano@gs1co.org',
            "password": 'kT43=gt29',
            "virtual_operator": 'saphety'
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, json=payload)
        response_data = json.loads(response.text)
        token = response_data['ResultData']['access_token']

        return token

    def _get_status_dian_by_cufe(self, token: str, cufe: str) -> str:
        url = f"https://api-factura-electronica-co.saphety.com/v2/saphety/outbounddocuments/{cufe}"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        }
        status_dian = None
        response = requests.request("GET", url, headers=headers)
        response_data = json.loads(response.text)
        if response_data and response_data['ResultData']:
            status_dian = response_data['ResultData']['DocumentStatus']

        return status_dian

    def cron_update_invoice_status(self):
        invoices = self.env['account.move'].search([
            ('create_date', '>=', '2024-01-01'),
            ('state', '=', 'posted'),
            ('x_status_dian', '=', False),
            ('name', 'like', 'FEC%')
        ], limit=20)
        
        token = self._get_token()
        if token:
            for invoice in invoices:
                status_dian = self._get_status_dian_by_cufe(token, invoice.x_cufe_dian)
                if status_dian:
                    self._update_status_dian(invoice, status_dian)
    
    def _update_status_dian(self, invoice, status_dian):
        invoice.x_status_dian = status_dian

    @api.depends('x_value_discounts')
    def _compute_amount_total_discounts(self):
        amount_total_discounts = 0
        for record in self:
            amount_total = record.amount_total
            conditional_discount = record.x_value_discounts
            amount_total_discounts = amount_total-conditional_discount
            record.x_amount_total_discounts = amount_total_discounts
    
    def create_approval_request(self):
        ctx = self.env.context.copy()
        
        #Traer categoria de aprobación de NC
        obj_category_approval = self.env['approval.category'].search([('x_approval_nc', '=', True)])
        id_category = 0
        for category in obj_category_approval:
            id_category = category.id
        
        #Traer usuario logeado
        user_id = self.env.user
        
        ctx.update({'x_account_move_id':self.id,'category_id':id_category,'request_owner_id':user_id.id})
        self.env['approval.request'].with_context(ctx).init()
        return {
            'type': 'ir.actions.act_window',
            'name': 'All Approvals',
            'res_model': 'approval.request',
            'domain': [],
            'view_mode': 'form',
            'context': ctx,
            'target': 'current',
        }
    
    def _have_approval_request(self):
        query_have_approval = '''
            Select id,"name" 
            From approval_request 
            Where x_account_move_id = %s
        ''' % (self.id)
        
        self._cr.execute(query_have_approval)
        result_query_have_approval = self._cr.dictfetchall()
        
        if result_query_have_approval:
            self.x_have_approval_request = True
            self.x_create_approval_request = True
        else:
            self.x_have_approval_request = False
            self.x_create_approval_request = False
        
        query_approval = '''
            Select id,"name" 
            From approval_request 
            Where request_status = 'approved' and x_account_move_id = %s
        ''' % (self.id)
        
        self._cr.execute(query_approval)
        result_query_approval = self._cr.dictfetchall()
        
        if result_query_approval or self.x_is_mass_billing:
            self.x_approved_approval_request = True
        else:
            self.x_approved_approval_request = False   
    
    
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
    
    @api.onchange('invoice_origin')
    def _onchange_invoice_origin_country(self):
        
        if self.invoice_origin:
            country_id = 0
            sale_order = self.env['sale.order'].search([('name', '=', self.invoice_origin)])        
            purchase_order = self.env['purchase.order'].search([('name', '=', self.invoice_origin)])        
        
            if sale_order:
                country_id = sale_order.x_country_account_id.id
            if purchase_order:
                country_id = purchase_order.x_country_account_id.id
            
            if country_id != 0:
                values = {
                        'x_country_account_id': country_id ,                
                    }
                self.update(values)
    
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
        if self.move_type == 'out_invoice' or self.move_type == 'out_refund' or self.move_type == 'out_receipt':            
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
                    if i.type_fe:
                        cant_contactsFE = cant_contactsFE + 1
                        if not record.name:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene nombre, por favor verificar.'))     
                        if record.x_active_for_logyca == False:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no esta activo, por favor verificar.'))    
                        # if not record.street:
                        #     raise ValidationError(_('El contacto de tipo facturación electrónica no tiene dirección, por favor verificar.'))    
                        # if not record.x_city:
                        #     raise ValidationError(_('El contacto de tipo facturación electrónica no tiene ciudad, por favor verificar.'))    
                        if not record.email:
                            raise ValidationError(_('El contacto de tipo facturación electrónica no tiene email, por favor verificar.'))    
                        # if not record.phone and not record.mobile:
                        #     raise ValidationError(_('El contacto de tipo facturación electrónica no tiene teléfono, por favor verificar.'))
                        
            if cant_contactsFE == 0:
                raise ValidationError(_('El cliente al que pertenece la factura no tiene un contacto de tipo facturación electrónica, por favor verificar.'))     
        
        return super(AccountMove, self).action_post()
    
    #Se comenta validación para el formato de impresión y de esta forma imprimir todo tipo de movimientos - 25/09/2020
    def _get_report_base_filename(self):
        #if any(not move.is_invoice() for move in self):
        #    raise UserError(_("Only invoices could be printed."))
        return self._get_move_display_name()
    
    #Se reemplaza codigo de _auto_create_asset debido a modificacion del codigo por parte de Odoo que afecto nuestro funcionamiento normal
    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        for move in self:
            if not move.is_invoice():
                continue

            for move_line in move.line_ids:
                if (
                    move_line.account_id
                    and (move_line.account_id.can_create_asset)
                    and move_line.account_id.create_asset != "no"
                    and not move.reversed_entry_id
                    and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                    and not move_line.asset_ids
                ):
                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    vals = {
                        'name': move_line.name,
                        'company_id': move_line.company_id.id,
                        'currency_id': move_line.company_currency_id.id,
                        'original_move_line_ids': [(6, False, move_line.ids)],
                        'state': 'draft',
                    }
                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                        })
                    auto_validate.append(move_line.account_id.create_asset == 'validate')
                    invoice_list.append(move)
                    create_list.append(vals)

        assets = self.env['account.asset'].create(create_list)
        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals:
                asset._onchange_model_id()
                # asset._onchange_method_period()
                if validate:
                    asset.validate()
            if invoice:
                asset_name = {
                    'purchase': _('Asset'),
                    'sale': _('Deferred revenue'),
                    'expense': _('Deferred expense'),
                }[asset.asset_type]
                msg = _('%s created from invoice') % (asset_name)
                msg += ': <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>' % (invoice.id, invoice.name)
                asset.message_post(body=msg)
        return assets
    
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
                    
        #Validar que reverse los ingresos diferidos ya publicados
        query_assets = '''
                Select d.id
                From account_move a 
                inner join account_move_line b on a.id = b.move_id
                inner join account_asset c on b.asset_id = c.id
                inner join account_move d on c.id = d.asset_id
                where a.id = %s and d.state = 'posted'
        ''' % (self.move_id.id)
        
        self._cr.execute(query_assets)
        result_query_assets = self._cr.dictfetchall()
        
        if result_query_assets:
            for assets in result_query_assets:        
                    self.env.context['active_ids'].append(assets.get("id"))        
        
        #Guardar en un array los ingresos diferidos en borrador para eliminar
        assets_draft_detele = []
        query_assets_draft = '''
                Select d.id
                From account_move a 
                inner join account_move_line b on a.id = b.move_id
                inner join account_asset c on b.asset_id = c.id
                inner join account_move d on c.id = d.asset_id
                where a.id = %s and d.state = 'draft'
        ''' % (self.move_id.id)
        
        self._cr.execute(query_assets_draft)
        result_query_assets_draft = self._cr.dictfetchall()
        
        if result_query_assets_draft:
            for assets in result_query_assets_draft:    
                move_unlink = self.env['account.move'].search([('id', '=', assets.get("id"))])
                assets_draft_detele.append(move_unlink)
                #move_unlink.unlink()                   
        
        #Ejecutar metodo original
        method_original = super(AccountMoveReversal, self).reverse_moves()
        
        #Eliminar ingresos diferidos en borrador
        if result_query_assets:
            if assets_draft_detele:
                for assets_draft in assets_draft_detele:    
                    assets_draft.unlink()                   
        
        #Si es una NC de facturación masvia debe cancelar la orden de venta que se genero por este proceso
        id_nc = method_original.get('res_id')
        obj_nc = self.env['account.move'].search([('id', '=', id_nc)])
        if obj_nc.x_is_mass_billing == True:
            name_sale_order = obj_nc.invoice_origin
            partner_sale_order = obj_nc.partner_id.id
            company_sale_order = obj_nc.company_id.id
            obj_sale_order = self.env['sale.order'].search([('name', '=', name_sale_order),('partner_id.id','=',partner_sale_order),('company_id.id','=',company_sale_order)])
            obj_sale_order.action_cancel()
            
        return method_original        
        #return super(AccountMoveReversal, self).reverse_moves()
        
        
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
    product_categ_id_fam = fields.Many2one('product.category', string='Categoría de Producto / Familia', readonly=True)
    product_categ_id_lin = fields.Many2one('product.category', string='Categoría de Producto / Línea', readonly=True)
    #Red de valor
    x_analytic_account_id = fields.Many2one('account.analytic.account', string='Red de Valor', readonly=True)
        
    def _select(self):
        add_select = '''
            , move.analytic_account_id as x_analytic_account_id,
            partner.vat as x_vat,
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
            , move.analytic_account_id,partner.vat,analytic.group_id,analytic_group.parent_id,category_fam.id,category_lin.id
        '''
        return super(AccountInvoiceReport, self)._group_by() + add_group
    
#Lineas Analiticas
class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    x_groupline_id = fields.Many2one(string='Grupo Analítico / Línea', store=True, readonly=True, related='group_id.parent_id', change_default=True)    

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
    x_budget_group = fields.Many2one(string='Grupo presupuestal', readonly=True, related='original_move_line_ids.x_budget_group')
    x_partner = fields.Many2one('res.partner', string='Asociado')
    x_studio_accumulated_depreciation = fields.Float(string='Depreciación acumulada', default=0.0)
    x_studio_history_cost = fields.Float(string='Costo histórico', default=0.0)
    x_studio_asset_plate = fields.Char(string='Placa del activo')
    x_studio_serial = fields.Char(string='Serial')
    x_studio_date_depreciation = fields.Date(string='Fecha depreciación total')
    x_studio_fecha_de_compra_his = fields.Date(string='Fecha de Compra (Histórica)')
    x_studio_deprecieted_periods = fields.Integer(string='Periodos depreciados')
    x_studio_ussefull_life = fields.Integer(string='Vida útil')
    

#Plazos de pago
class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'
    
    x_is_mass_billing = fields.Boolean(string='Facturación masiva')   
    
#Plan contable
class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    x_discount_account = fields.Boolean(string='Cuenta asignada para descuento')   
    
    

        