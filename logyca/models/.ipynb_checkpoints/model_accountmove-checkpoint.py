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
    
    def reverse_moves(self):
        self.refund_method = 'cancel'
        return super(AccountMoveReversal, self).reverse_moves()
        
# Detalle Movimiento
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal', index=True, ondelete='restrict')
    # Fields Reports
    x_vat_partner = fields.Char(string='NIT Asociado', store=True, readonly=True, related='partner_id.vat', change_default=True)
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
    
class ReportAgedPartnerBalance(models.AbstractModel):
    _inherit = 'report.account.report_agedpartnerbalance'
    
    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        # In case of a period_length of 30 days as of 2019-02-08, we want the following periods:
        # Name       Stop         Start
        # 1 - 30   : 2019-02-07 - 2019-01-09
        # 31 - 60  : 2019-01-08 - 2018-12-10
        # 61 - 90  : 2018-12-09 - 2018-11-10
        # 91 - 120 : 2018-11-09 - 2018-10-11
        # +120     : 2018-10-10
        ctx = self._context
        periods = {}
        date_from = fields.Date.from_string(date_from)
        start = date_from
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            period_name = str((5-(i+1)) * period_length + 1) + '-' + str((5-i) * period_length)
            period_stop = (start - relativedelta(days=1)).strftime('%Y-%m-%d')
            if i == 0:
                period_name = '+' + str(4 * period_length)
            periods[str(i)] = {
                'name': period_name,
                'stop': period_stop,
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop

        res = []
        total = []
        partner_clause = ''
        cr = self.env.cr
        user_company = self.env.company
        user_currency = user_company.currency_id
        company_ids = self._context.get('company_ids') or [user_company.id]
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type), date_from, date_from,)
        if 'partner_ids' in ctx:
            if ctx['partner_ids']:
                partner_clause = 'AND (l.partner_id IN %s)'
                arg_list += (tuple(ctx['partner_ids'].ids),)
            else:
                partner_clause = 'AND l.partner_id IS NULL'
        if ctx.get('partner_categories'):
            partner_clause += 'AND (l.partner_id IN %s)'
            partner_ids = self.env['res.partner'].search([('category_id', 'in', ctx['partner_categories'].ids)]).ids
            arg_list += (tuple(partner_ids or [0]),)
        arg_list += (date_from, tuple(company_ids))

        query = '''
            SELECT DISTINCT l.partner_id, res_partner.vat ||' | '|| res_partner.name AS name, UPPER(res_partner.name) AS UPNAME, CASE WHEN prop.value_text IS NULL THEN 'normal' ELSE prop.value_text END AS trust
            FROM account_move_line AS l
              LEFT JOIN res_partner ON l.partner_id = res_partner.id
              LEFT JOIN ir_property prop ON (prop.res_id = 'res.partner,'||res_partner.id AND prop.name='trust' AND prop.company_id=%s),
              account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND (
                        l.reconciled IS FALSE
                        OR l.id IN(
                            SELECT credit_move_id FROM account_partial_reconcile where max_date > %s
                            UNION ALL
                            SELECT debit_move_id FROM account_partial_reconcile where max_date > %s
                        )
                    )
                    ''' + partner_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        arg_list = (self.env.company.id,) + arg_list
        
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners]
        lines = dict((partner['partner_id'], []) for partner in partners)
        if not partner_ids:
            return [], [], {}

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s
                    ORDER BY COALESCE(l.date_maturity, l.date)'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids).with_context(prefetch_fields=False):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
                if user_currency.is_zero(line_amount):
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
                for partial_line in line.matched_credit_ids:
                    if partial_line.max_date <= date_from:
                        line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)

                if not self.env.company.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines.setdefault(partner_id, [])
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) >= %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s
                ORDER BY COALESCE(l.date_maturity, l.date)'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.company_id.currency_id._convert(line.balance, user_currency, user_company, date_from)
            if user_currency.is_zero(line_amount):
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.max_date <= date_from:
                    line_amount += partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
            for partial_line in line.matched_credit_ids:
                if partial_line.max_date <= date_from:
                    line_amount -= partial_line.company_id.currency_id._convert(partial_line.amount, user_currency, user_company, date_from)
            if not self.env.company.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines.setdefault(partner_id, [])
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.company.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.company.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            # Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                #values['name'] = len(partner['name']) >= 45 and partner['name'][0:40] + '...' or partner['name']
                values['name'] = partner['name']
                values['trust'] = partner['trust']
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or (self._context.get('include_nullified_amount') and lines[partner['partner_id']]):
                res.append(values)
        
        return res, total, lines