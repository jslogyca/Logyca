# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlsxwriter
from io import BytesIO
from datetime import datetime


class ConditionalDiscountInvoiceLine(models.TransientModel):
    _name = 'conditional.discount.invoice.line'
    _description = 'Línea de Factura para Descuento Condicionado'

    wizard_id = fields.Many2one(
        'conditional.discount.report.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
        required=True,
        readonly=True
    )
    
    invoice_name = fields.Char(
        string='Número Factura',
        related='invoice_id.name',
        readonly=True
    )
    
    invoice_date = fields.Date(
        string='Fecha Factura',
        related='invoice_id.invoice_date',
        readonly=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        related='invoice_id.partner_id',
        readonly=True
    )
    
    discount_amount = fields.Float(
        string='Valor Descuento',
        required=True,
        readonly=True
    )
    
    payment_move_id = fields.Many2one(
        'account.move',
        string='Comprobante de Pago',
        readonly=True
    )
    
    payment_move_name = fields.Char(
        string='Número Pago',
        related='payment_move_id.name',
        readonly=True
    )
    
    discount_line_id = fields.Many2one(
        'account.move.line',
        string='Línea 530535',
        readonly=True
    )
    
    selected = fields.Boolean(
        string='Seleccionar',
        default=True
    )
    
    credit_note_id = fields.Many2one(
        'account.move',
        string='Nota Crédito',
        readonly=True
    )
    
    reversal_move_id = fields.Many2one(
        'account.move',
        string='Comprobante Reversión',
        readonly=True
    )
    
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('processed', 'Procesado'),
        ('error', 'Error')
    ], string='Estado', default='pending', readonly=True)
    
    error_message = fields.Text(
        string='Mensaje de Error',
        readonly=True
    )


class ConditionalDiscountReportWizard(models.TransientModel):
    _name = 'conditional.discount.report.wizard'
    _description = 'Wizard para Reporte de Descuentos Condicionados'

    year = fields.Integer(
        string='Año',
        required=True,
        default=2025
    )
    
    date_from = fields.Date(
        string='Fecha Desde',
        compute='_compute_dates',
        store=True
    )
    
    date_to = fields.Date(
        string='Fecha Hasta',
        compute='_compute_dates',
        store=True
    )
    
    reversal_journal_id = fields.Many2one(
        'account.journal',
        string='Diario para Comprobantes de Reversión',
        domain="[('type', '=', 'general')]",
        help='Diario donde se crearán los comprobantes contables de reversión (Solo requerido si va a procesar NC)'
    )
    
    discount_account_id = fields.Many2one(
        'account.account',
        string='Cuenta de Descuentos (530535)',
        domain="[('code', '=', '530535')]",
        required=True,
        help='Cuenta 530535 - Descuentos Comerciales Condicionados'
    )
    
    source_move_id = fields.Many2one(
        'account.move',
        string='Asiento Contable Fuente',
        domain="[('state', '=', 'posted')]",
        help='Asiento contable que contiene en sus líneas el número de factura en el campo name (ej: DTO POR PRONTO PAGO DEL 1-16 ENERO _ MERCADO PAGO FEC/2025/251629)'
    )
    
    source_type = fields.Selection([
        ('payment_reconciliation', 'Desde Pagos Conciliados'),
        ('accounting_entry', 'Desde Asiento Contable')
    ], string='Origen de Datos', default='payment_reconciliation')
    
    invoice_line_ids = fields.One2many(
        'conditional.discount.invoice.line',
        'wizard_id',
        string='Facturas para Procesar'
    )
    
    excel_file = fields.Binary(
        string='Archivo Excel',
        readonly=True
    )
    
    excel_filename = fields.Char(
        string='Nombre del Archivo',
        readonly=True
    )
    
    records_found = fields.Integer(
        string='Registros Encontrados',
        readonly=True
    )
    
    records_excluded = fields.Integer(
        string='Registros Excluidos',
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('loaded', 'Facturas Cargadas'),
        ('done', 'Completado')
    ], default='draft', string='Estado')

    @api.depends('year')
    def _compute_dates(self):
        for record in self:
            if record.year:
                record.date_from = fields.Date.from_string(f'{record.year}-01-01')
                record.date_to = fields.Date.from_string(f'{record.year}-12-31')
            else:
                record.date_from = False
                record.date_to = False

    def action_generate_excel_only(self):
        """Generar solo el reporte Excel sin crear NC ni comprobantes"""
        self.ensure_one()
        
        # Validar configuración
        if not self.discount_account_id:
            raise UserError(_('Debe seleccionar la cuenta de descuentos condicionados (530535)'))
        
        # Buscar apuntes que cumplan los criterios
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('account_id', '=', self.discount_account_id.id),
            ('journal_id.type', '=', 'bank'),
            ('debit', '>', 0),
        ]
        
        lines_530535 = self.env['account.move.line'].search(domain)
        
        if not lines_530535:
            raise UserError(
                _('No se encontraron descuentos condicionados que cumplan los criterios para el año %s') % self.year
            )
        
        # Procesar cada línea y consolidar información
        report_data = []
        excluded_count = 0
        
        for line in lines_530535:
            # Identificar factura relacionada
            invoice = self._get_related_invoice(line)
            
            if not invoice:
                excluded_count += 1
                continue
            
            # Buscar si ya existe nota crédito creada por este proceso
            existing_credit_note = self.env['account.move'].search([
                ('reversed_entry_id', '=', invoice.id),
                ('move_type', '=', 'out_refund'),
                ('is_conditional_discount_credit_note', '=', True),
                ('state', '=', 'posted')
            ], limit=1)
            
            # Buscar comprobante de reversión si existe NC
            reversal_move = False
            if existing_credit_note:
                # Buscar comprobante con referencia a la factura en el diario de reversión
                reversal_move = self.env['account.move'].search([
                    ('move_type', '=', 'entry'),
                    ('ref', '=', invoice.name),
                    ('state', '=', 'posted'),
                    ('line_ids.account_id.code', '=', '530535'),
                    ('line_ids.credit', '>', 0),
                ], limit=1)
            
            # Determinar estado
            if existing_credit_note:
                state = 'Ya Procesada'
            else:
                state = 'Pendiente de Procesar'
            
            # Consolidar información
            report_data.append({
                'invoice_number': invoice.name or '',
                'invoice_date': invoice.invoice_date or invoice.date,
                'partner_name': invoice.partner_id.name or '',
                'partner_vat': invoice.partner_id.vat or '',
                'currency': invoice.currency_id.name or '',
                'factura_total_moneda': invoice.amount_untaxed or 0,
                'factura_total': invoice.amount_total or 0,
                'factura_total_compania': invoice.amount_total_signed or 0,
                'pay_move_name': line.move_id.name or '',
                'pay_move_date': line.move_id.date,
                'valor_530535_debito': line.debit or 0,
                'credit_note_number': existing_credit_note.name if existing_credit_note else '',
                'credit_note_amount': existing_credit_note.amount_total if existing_credit_note else 0,
                'reversal_move_number': reversal_move.name if reversal_move else '',
                'reversal_move_amount': line.debit if reversal_move else 0,
                'state': state,
                'error_message': '',
            })
        
        if not report_data:
            raise UserError(
                _('No se encontraron registros conciliados con facturas de venta.')
            )
        
        # Generar Excel
        excel_file = self._generate_excel(report_data)
        
        # Actualizar wizard con el archivo
        filename = f'Descuentos_Condicionados_Reporte_{self.year}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        self.write({
            'excel_file': base64.b64encode(excel_file),
            'excel_filename': filename,
            'records_found': len(report_data),
            'records_excluded': excluded_count,
            'state': 'done'
        })
        
        # Retornar la vista actualizada del wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_load_invoices(self):
        """Cargar facturas que cumplen los criterios"""
        self.ensure_one()
        
        # Validar configuración
        if not self.reversal_journal_id:
            raise UserError(_('Debe seleccionar un diario para los comprobantes de reversión'))
        
        if not self.discount_account_id:
            raise UserError(_('Debe seleccionar la cuenta de descuentos condicionados (530535)'))
        
        # Limpiar líneas anteriores
        self.invoice_line_ids.unlink()
        
        # Buscar apuntes que cumplan los criterios
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('account_id', '=', self.discount_account_id.id),
            ('journal_id.type', '=', 'bank'),
            ('debit', '>', 0),
        ]
        
        lines_530535 = self.env['account.move.line'].search(domain)
        
        if not lines_530535:
            raise UserError(
                _('No se encontraron descuentos condicionados que cumplan los criterios para el año %s') % self.year
            )
        
        # Procesar cada línea y crear líneas de wizard
        invoice_lines = []
        excluded_count = 0
        processed_invoices = set()
        
        for line in lines_530535:
            # Identificar factura relacionada
            invoice = self._get_related_invoice(line)
            
            if not invoice:
                excluded_count += 1
                continue
            
            # Evitar duplicados (una factura puede tener múltiples descuentos)
            if invoice.id in processed_invoices:
                continue
            
            processed_invoices.add(invoice.id)
            
            # Verificar si ya tiene nota crédito creada por este proceso
            existing_credit_note = self.env['account.move'].search([
                ('reversed_entry_id', '=', invoice.id),
                ('move_type', '=', 'out_refund'),
                ('is_conditional_discount_credit_note', '=', True),
                ('state', '=', 'posted')
            ], limit=1)
            
            if existing_credit_note:
                excluded_count += 1
                continue
            
            # Crear línea de wizard
            invoice_lines.append((0, 0, {
                'invoice_id': invoice.id,
                'discount_amount': line.debit,
                'payment_move_id': line.move_id.id,
                'discount_line_id': line.id,
                'selected': True,
                'state': 'pending'
            }))
        
        if not invoice_lines:
            raise UserError(
                _('No se encontraron facturas elegibles. Todas las facturas ya tienen notas crédito generadas o no están conciliadas.')
            )
        
        # Crear líneas
        self.write({
            'invoice_line_ids': invoice_lines,
            'records_found': len(invoice_lines),
            'records_excluded': excluded_count,
            'state': 'loaded'
        })
        
        # Retornar vista con facturas cargadas
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_unselect_all(self):
        """Deseleccionar todas las facturas"""
        self.ensure_one()
        self.invoice_line_ids.write({'selected': False})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_load_invoices_from_move(self):
        """Cargar facturas para procesar desde un asiento contable"""
        self.ensure_one()
        
        # Validar configuración
        if not self.reversal_journal_id:
            raise UserError(_('Debe seleccionar el Diario para Comprobantes de Reversión'))
        
        if not self.discount_account_id:
            raise UserError(_('Debe seleccionar la cuenta de descuentos condicionados (530535)'))
        
        if not self.source_move_id:
            raise UserError(_('Debe seleccionar el Asiento Contable Fuente'))
        
        # Limpiar líneas anteriores
        self.invoice_line_ids.unlink()
        
        # Obtener líneas del asiento que contengan número de factura
        move_lines = self.source_move_id.line_ids.filtered(
            lambda l: l.account_id == self.discount_account_id and l.name and 'FEC/' in l.name
        )
        
        if not move_lines:
            raise UserError(
                _('No se encontraron líneas con número de factura en el asiento seleccionado.\n\n'
                  'Verifique que:\n'
                  '- Las líneas usen la cuenta de descuentos (530535)\n'
                  '- El campo "Etiqueta" contenga el número de factura\n'
                  '- El formato sea: "DTO POR PRONTO PAGO DEL 1-16 ENERO _ MERCADO PAGO FEC/2025/251629"')
            )
        
        # Procesar cada línea y crear líneas de wizard
        invoice_lines = []
        excluded_count = 0
        processed_invoices = set()
        errors = []
        
        for line in move_lines:
            # Extraer número de factura del campo name
            invoice_number = self._extract_invoice_number_from_line(line.name)
            
            if not invoice_number:
                excluded_count += 1
                errors.append(f"Línea '{line.name}': No se pudo extraer número de factura")
                continue
            
            # Buscar la factura por número
            invoice = self.env['account.move'].search([
                ('name', '=', invoice_number),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], limit=1)
            
            if not invoice:
                excluded_count += 1
                errors.append(f"Factura {invoice_number}: No encontrada o no está contabilizada")
                continue
            
            # Evitar duplicados
            if invoice.id in processed_invoices:
                excluded_count += 1
                errors.append(f"Factura {invoice_number}: Duplicada en el asiento")
                continue
            
            processed_invoices.add(invoice.id)
            
            # Buscar si ya existe nota crédito creada por este proceso
            existing_credit_note = self.env['account.move'].search([
                ('reversed_entry_id', '=', invoice.id),
                ('move_type', '=', 'out_refund'),
                ('is_conditional_discount_credit_note', '=', True),
                ('state', '=', 'posted')
            ], limit=1)
            
            # Buscar si ya existe comprobante de reversión
            existing_reversal = self.env['account.move'].search([
                ('ref', 'like', f'Reversión DTO Condicionado - {invoice.name}'),
                ('journal_id', '=', self.reversal_journal_id.id),
                ('state', '=', 'posted')
            ], limit=1)
            
            # Si ya existe NC o comprobante, excluir
            if existing_credit_note or existing_reversal:
                excluded_count += 1
                errors.append(f"Factura {invoice_number}: Ya tiene NC o comprobante de reversión")
                continue
            
            # Obtener monto del descuento (puede estar en débito o crédito)
            discount_amount = abs(line.debit - line.credit)
            
            # Crear línea de wizard
            invoice_lines.append((0, 0, {
                'invoice_id': invoice.id,
                'discount_amount': discount_amount,
                'payment_move_id': self.source_move_id.id,
                'discount_line_id': line.id,
                'selected': True,
                'state': 'pending'
            }))
        
        if not invoice_lines:
            error_msg = 'No se encontraron facturas elegibles para procesar.\n\n'
            if errors:
                error_msg += 'Razones de exclusión:\n' + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_msg += f'\n... y {len(errors) - 10} más'
            raise UserError(_(error_msg))
        
        # Crear líneas
        self.write({
            'invoice_line_ids': invoice_lines,
            'records_found': len(move_lines),
            'records_excluded': excluded_count,
            'state': 'loaded',
            'source_type': 'accounting_entry'
        })
        
        # Retornar vista con facturas cargadas
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _extract_invoice_number_from_line(self, line_name):
        """
        Extrae el número de factura del campo name de una línea contable
        Formato esperado: "DTO POR PRONTO PAGO DEL 1-16 ENERO _ MERCADO PAGO FEC/2025/251629"
        Retorna: "FEC/2025/251629"
        """
        import re
        if not line_name:
            return None
        
        # Buscar patrón FEC/YYYY/NNNNNN o FEC-YYYY-NNNNNN
        pattern = r'FEC[/-]\d{4}[/-]\d+'
        match = re.search(pattern, line_name)
        
        if match:
            invoice_number = match.group()
            # Normalizar separadores a /
            invoice_number = invoice_number.replace('-', '/')
            return invoice_number
        
        return None
    
    def action_select_all(self):
        """Seleccionar todas las facturas"""
        self.ensure_one()
        self.invoice_line_ids.write({'selected': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_process_credit_notes(self):
        """Procesar y crear notas crédito y comprobantes"""
        self.ensure_one()
        
        selected_lines = self.invoice_line_ids.filtered(lambda l: l.selected and l.state == 'pending')
        
        if not selected_lines:
            raise UserError(_('No hay facturas seleccionadas para procesar'))
        
        errors = []
        processed_count = 0
        
        for line in selected_lines:
            try:
                # Validación previa: verificar que la factura no tenga ya NC o comprobante
                invoice = line.invoice_id
                
                # Buscar NC existente
                existing_credit_note = self.env['account.move'].search([
                    ('reversed_entry_id', '=', invoice.id),
                    ('move_type', '=', 'out_refund'),
                    ('is_conditional_discount_credit_note', '=', True),
                    ('state', '=', 'posted')
                ], limit=1)
                
                if existing_credit_note:
                    raise UserError(_(
                        f'La factura {invoice.name} ya tiene una Nota Crédito generada '
                        f'por este proceso: {existing_credit_note.name}'
                    ))
                
                # Buscar comprobante de reversión existente
                existing_reversal = self.env['account.move'].search([
                    ('ref', '=', invoice.name),
                    ('journal_id', '=', self.reversal_journal_id.id),
                    ('state', '=', 'posted')
                ], limit=1)
                
                if existing_reversal:
                    raise UserError(_(
                        f'La factura {invoice.name} ya tiene un Comprobante de Reversión '
                        f'generado: {existing_reversal.name}'
                    ))
                
                # Crear nota crédito
                credit_note = self._create_credit_note(line)
                
                # Crear comprobante de reversión
                reversal_move = self._create_reversal_entry(line, credit_note)
                
                # Conciliar CXC de NC con CXC del comprobante (NO con la factura)
                self._reconcile_entries(credit_note, reversal_move)
                
                # Actualizar línea
                line.write({
                    'credit_note_id': credit_note.id,
                    'reversal_move_id': reversal_move.id,
                    'state': 'processed'
                })
                
                processed_count += 1
                
            except Exception as e:
                # Si hay error, intentar eliminar documentos creados
                try:
                    if 'credit_note' in locals() and credit_note and credit_note.state == 'posted':
                        credit_note.button_draft()
                        credit_note.button_cancel()
                    if 'reversal_move' in locals() and reversal_move and reversal_move.state == 'posted':
                        reversal_move.button_draft()
                        reversal_move.button_cancel()
                except:
                    pass
                
                line.write({
                    'state': 'error',
                    'error_message': str(e)
                })
                errors.append(f"Factura {line.invoice_name}: {str(e)}")
        
        # Generar reporte Excel
        report_data = self._prepare_report_data()
        excel_file = self._generate_excel(report_data)
        filename = f'Descuentos_Condicionados_{self.year}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        self.write({
            'excel_file': base64.b64encode(excel_file),
            'excel_filename': filename,
            'state': 'done'
        })
        
        # Mostrar mensaje según resultado
        if errors:
            message = f'Se procesaron {processed_count} de {len(selected_lines)} facturas.\n\nErrores:\n' + '\n'.join(errors[:5])
            if len(errors) > 5:
                message += f'\n... y {len(errors) - 5} errores más (ver reporte Excel)'
            raise UserError(_(message))
        
        # Retornar vista actualizada del wizard
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def _create_credit_note(self, line):
        """Crear nota crédito para una factura"""
        invoice = line.invoice_id
        
        # Obtener cuenta CXC de la factura
        receivable_line = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        )
        
        if not receivable_line:
            raise UserError(_('No se encontró línea de CXC en la factura %s') % invoice.name)
        
        receivable_account = receivable_line[0].account_id
        
        # Obtener cuenta de ingresos (primera línea que no sea CXC ni impuestos)
        income_line = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type in ('income', 'income_other') and not l.tax_line_id
        )
        
        if not income_line:
            raise UserError(_('No se encontró cuenta de ingresos en la factura %s') % invoice.name)
        
        income_account = income_line[0].account_id
        
        # Crear nota crédito
        credit_note_vals = {
            'move_type': 'out_refund',
            'partner_id': invoice.partner_id.id,
            'invoice_payment_term_id': invoice.invoice_payment_term_id.id,
            'invoice_date': fields.Date.today(),
            'date': fields.Date.today(),
            'ref': 'Reversión de: ' + invoice.name,
            'x_num_order_purchase': 'Reversión de: ' + invoice.name,
            'reversed_entry_id': invoice.id,
            'is_conditional_discount_credit_note': True,
            'invoice_line_ids': [(0, 0, {
                'name': f'Descuento Condicionado - {invoice.name}',
                'quantity': 1,
                'price_unit': line.discount_amount,
                'account_id': income_account.id,
                'analytic_distribution': income_line[0].analytic_distribution or False,
            })]
        }
        
        credit_note = self.env['account.move'].create(credit_note_vals)
        credit_note.action_post()
        
        return credit_note
    
    def _create_reversal_entry(self, line, credit_note):
        """Crear comprobante contable de reversión"""
        invoice = line.invoice_id
        
        # Obtener cuenta CXC de la factura
        receivable_line = invoice.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        )
        receivable_account = receivable_line[0].account_id
        
        # Obtener analítica de la factura
        analytic_distribution = False
        for inv_line in invoice.line_ids:
            if inv_line.analytic_distribution:
                analytic_distribution = inv_line.analytic_distribution
                break
        
        # Crear comprobante
        reversal_vals = {
            'move_type': 'entry',
            'journal_id': self.reversal_journal_id.id,
            'date': fields.Date.today(),
            'ref': invoice.name,
            'line_ids': [
                # Débito a CXC
                (0, 0, {
                    'name': f'Reversion Descuento Condicionado - {invoice.name}',
                    'account_id': receivable_account.id,
                    'partner_id': invoice.partner_id.id,
                    'debit': line.discount_amount,
                    'credit': 0,
                    'analytic_distribution': analytic_distribution,
                }),
                # Crédito a cuenta 530535
                (0, 0, {
                    'name': f'Reversion Descuento Condicionado - {invoice.name}',
                    'account_id': self.discount_account_id.id,
                    'partner_id': invoice.partner_id.id,
                    'debit': 0,
                    'credit': line.discount_amount,
                    'analytic_distribution': analytic_distribution,
                })
            ]
        }
        
        reversal_move = self.env['account.move'].create(reversal_vals)
        reversal_move.action_post()
        
        return reversal_move
    
    def _reconcile_entries(self, credit_note, reversal_move):
        """Conciliar la CXC de la nota crédito con la CXC del comprobante"""
        # Obtener línea CXC de la nota crédito
        cn_receivable_line = credit_note.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        )
        
        # Obtener línea CXC del comprobante de reversión
        reversal_receivable_line = reversal_move.line_ids.filtered(
            lambda l: l.account_id.account_type == 'asset_receivable'
        )
        
        if cn_receivable_line and reversal_receivable_line:
            # Conciliar
            lines_to_reconcile = cn_receivable_line | reversal_receivable_line
            lines_to_reconcile.reconcile()
    
    def _prepare_report_data(self):
        """Preparar datos para el reporte Excel"""
        report_data = []
        
        for line in self.invoice_line_ids:
            invoice = line.invoice_id
            
            report_data.append({
                'invoice_number': invoice.name or '',
                'invoice_date': invoice.invoice_date or invoice.date,
                'partner_name': invoice.partner_id.name or '',
                'partner_vat': invoice.partner_id.vat or '',
                'currency': invoice.currency_id.name or '',
                'factura_total_moneda': invoice.amount_untaxed or 0,
                'factura_total': invoice.amount_total or 0,
                'factura_total_compania': invoice.amount_total_signed or 0,
                'pay_move_name': line.payment_move_name or '',
                'pay_move_date': line.payment_move_id.date if line.payment_move_id else False,
                'valor_530535_debito': line.discount_amount or 0,
                'credit_note_number': line.credit_note_id.name if line.credit_note_id else '',
                'credit_note_amount': line.credit_note_id.amount_total if line.credit_note_id else 0,
                'reversal_move_number': line.reversal_move_id.name if line.reversal_move_id else '',
                'reversal_move_amount': line.discount_amount if line.reversal_move_id else 0,
                'state': dict(line._fields['state'].selection).get(line.state, ''),
                'error_message': line.error_message or '',
            })
        
        return report_data

    def _get_related_invoice(self, line):
        """
        Identifica la factura de venta relacionada con el apunte de descuento
        a través de la conciliación
        """
        # Buscar por conciliación completa
        if line.full_reconcile_id:
            reconciled_lines = self.env['account.move.line'].search([
                ('full_reconcile_id', '=', line.full_reconcile_id.id),
                ('move_id.move_type', '=', 'out_invoice'),
                ('move_id.state', '=', 'posted')
            ])
            if reconciled_lines:
                return reconciled_lines[0].move_id
        
        # Buscar por conciliación parcial (matched_debit_ids / matched_credit_ids)
        # Primero verificar matched_debit_ids
        for match in line.matched_debit_ids:
            debit_line = match.debit_move_id
            if debit_line.move_id.move_type == 'out_invoice' and debit_line.move_id.state == 'posted':
                return debit_line.move_id
            credit_line = match.credit_move_id
            if credit_line.move_id.move_type == 'out_invoice' and credit_line.move_id.state == 'posted':
                return credit_line.move_id
        
        # Verificar matched_credit_ids
        for match in line.matched_credit_ids:
            debit_line = match.debit_move_id
            if debit_line.move_id.move_type == 'out_invoice' and debit_line.move_id.state == 'posted':
                return debit_line.move_id
            credit_line = match.credit_move_id
            if credit_line.move_id.move_type == 'out_invoice' and credit_line.move_id.state == 'posted':
                return credit_line.move_id
        
        # Buscar líneas del mismo movimiento que estén conciliadas con facturas
        payment_move = line.move_id
        for move_line in payment_move.line_ids:
            if move_line.account_id.account_type == 'asset_receivable':
                # Revisar conciliación completa
                if move_line.full_reconcile_id:
                    reconciled_lines = self.env['account.move.line'].search([
                        ('full_reconcile_id', '=', move_line.full_reconcile_id.id),
                        ('move_id.move_type', '=', 'out_invoice'),
                        ('move_id.state', '=', 'posted')
                    ])
                    if reconciled_lines:
                        return reconciled_lines[0].move_id
                
                # Revisar conciliaciones parciales
                for match in move_line.matched_debit_ids + move_line.matched_credit_ids:
                    for test_line in [match.debit_move_id, match.credit_move_id]:
                        if test_line.move_id.move_type == 'out_invoice' and test_line.move_id.state == 'posted':
                            return test_line.move_id
        
        return None

    def _generate_excel(self, data):
        """
        Genera el archivo Excel con los datos del reporte
        Crea dos hojas si el origen es desde asiento contable
        """
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        # Determinar nombre de la primera hoja según el origen
        if self.source_type == 'accounting_entry':
            worksheet1_name = 'Pagos Conciliados'
            worksheet2_name = 'Desde Asiento Contable'
        else:
            worksheet1_name = 'Descuentos Condicionados'
            worksheet2_name = None
        
        worksheet = workbook.add_worksheet(worksheet1_name)
        
        # Formatos
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D3D3D3',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True
        })
        
        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'border': 1,
            'align': 'center'
        })
        
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right'
        })
        
        text_format = workbook.add_format({
            'border': 1,
            'align': 'left',
            'valign': 'vcenter'
        })
        
        # Encabezados
        headers = [
            'Factura de Venta',
            'Fecha Factura',
            'Cliente',
            'NIT Cliente',
            'Moneda Factura',
            'Subtotal Factura',
            'Total Factura',
            'Total Factura (Moneda Cía)',
            'Comprobante Pago',
            'Fecha Pago',
            'Valor Descuento',
            'Nota Crédito',
            'Valor NC',
            'Comprobante Reversión',
            'Valor Reversión',
            'Estado',
            'Error'
        ]
        
        # Si el origen es desde asiento contable, agregar columna de origen
        if self.source_type == 'accounting_entry':
            headers.insert(8, 'Origen')
        
        # Escribir encabezados en la primera hoja
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 18)   # Factura de Venta
        worksheet.set_column(1, 1, 14)   # Fecha Factura
        worksheet.set_column(2, 2, 30)   # Cliente
        worksheet.set_column(3, 3, 15)   # NIT Cliente
        worksheet.set_column(4, 4, 12)   # Moneda Factura
        worksheet.set_column(5, 5, 16)   # Subtotal Factura
        worksheet.set_column(6, 6, 16)   # Total Factura
        worksheet.set_column(7, 7, 20)   # Total Factura (Moneda Cía)
        if self.source_type == 'accounting_entry':
            worksheet.set_column(8, 8, 25)   # Origen
            worksheet.set_column(9, 9, 18)   # Comprobante Pago
            worksheet.set_column(10, 10, 14) # Fecha Pago
            worksheet.set_column(11, 11, 16) # Valor Descuento
            worksheet.set_column(12, 12, 18) # Nota Crédito
            worksheet.set_column(13, 13, 14) # Valor NC
            worksheet.set_column(14, 14, 22) # Comprobante Reversión
            worksheet.set_column(15, 15, 16) # Valor Reversión
            worksheet.set_column(16, 16, 12) # Estado
            worksheet.set_column(17, 17, 30) # Error
        else:
            worksheet.set_column(8, 8, 18)   # Comprobante Pago
            worksheet.set_column(9, 9, 14)   # Fecha Pago
            worksheet.set_column(10, 10, 16) # Valor Descuento
            worksheet.set_column(11, 11, 18) # Nota Crédito
            worksheet.set_column(12, 12, 14) # Valor NC
            worksheet.set_column(13, 13, 22) # Comprobante Reversión
            worksheet.set_column(14, 14, 16) # Valor Reversión
            worksheet.set_column(15, 15, 12) # Estado
            worksheet.set_column(16, 16, 30) # Error
        
        # Escribir datos en la primera hoja
        self._write_excel_data(worksheet, data, text_format, date_format, number_format, 
                               include_origin=(self.source_type == 'accounting_entry'))
        
        # Si el origen es desde asiento contable, crear segunda hoja con información del asiento
        if self.source_type == 'accounting_entry' and self.source_move_id:
            worksheet2 = workbook.add_worksheet(worksheet2_name)
            self._write_source_move_sheet(worksheet2, workbook, header_format, text_format, 
                                         date_format, number_format)
        
        workbook.close()
        output.seek(0)
        return output.read()
    
    def _write_excel_data(self, worksheet, data, text_format, date_format, number_format, include_origin=False):
        """Escribe los datos en una hoja de Excel"""
        row = 1
        for record in data:
            col = 0
            worksheet.write(row, col, record['invoice_number'], text_format)
            col += 1
            
            if record['invoice_date']:
                if isinstance(record['invoice_date'], str):
                    invoice_date = datetime.strptime(record['invoice_date'], '%Y-%m-%d')
                else:
                    invoice_date = record['invoice_date']
                worksheet.write_datetime(row, col, invoice_date, date_format)
            else:
                worksheet.write(row, col, '', text_format)
            col += 1
            
            worksheet.write(row, col, record['partner_name'], text_format)
            col += 1
            worksheet.write(row, col, record['partner_vat'], text_format)
            col += 1
            worksheet.write(row, col, record['currency'], text_format)
            col += 1
            worksheet.write(row, col, record['factura_total_moneda'], number_format)
            col += 1
            worksheet.write(row, col, record['factura_total'], number_format)
            col += 1
            worksheet.write(row, col, record['factura_total_compania'], number_format)
            col += 1
            
            # Si incluye origen, agregar columna
            if include_origin:
                origen = 'Asiento Contable' if self.source_type == 'accounting_entry' else 'Pago Conciliado'
                worksheet.write(row, col, origen, text_format)
                col += 1
            
            worksheet.write(row, col, record['pay_move_name'], text_format)
            col += 1
            
            if record['pay_move_date']:
                if isinstance(record['pay_move_date'], str):
                    pay_date = datetime.strptime(record['pay_move_date'], '%Y-%m-%d')
                else:
                    pay_date = record['pay_move_date']
                worksheet.write_datetime(row, col, pay_date, date_format)
            else:
                worksheet.write(row, col, '', text_format)
            col += 1
            
            worksheet.write(row, col, record['valor_530535_debito'], number_format)
            col += 1
            worksheet.write(row, col, record.get('credit_note_number', ''), text_format)
            col += 1
            worksheet.write(row, col, record.get('credit_note_amount', 0), number_format)
            col += 1
            worksheet.write(row, col, record.get('reversal_move_number', ''), text_format)
            col += 1
            worksheet.write(row, col, record.get('reversal_move_amount', 0), number_format)
            col += 1
            worksheet.write(row, col, record.get('state', ''), text_format)
            col += 1
            worksheet.write(row, col, record.get('error_message', ''), text_format)
            
            row += 1
    
    def _write_source_move_sheet(self, worksheet, workbook, header_format, text_format, 
                                  date_format, number_format):
        """Escribe información del asiento contable fuente en una segunda hoja"""
        # Título
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter'
        })
        
        worksheet.merge_range('A1:E1', 'INFORMACIÓN DEL ASIENTO CONTABLE FUENTE', title_format)
        
        # Información del asiento
        info_label_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E7E6E6',
            'border': 1
        })
        
        info_value_format = workbook.add_format({
            'border': 1
        })
        
        row = 2
        worksheet.write(row, 0, 'Número de Asiento:', info_label_format)
        worksheet.write(row, 1, self.source_move_id.name, info_value_format)
        row += 1
        
        worksheet.write(row, 0, 'Fecha:', info_label_format)
        worksheet.write_datetime(row, 1, self.source_move_id.date, date_format)
        row += 1
        
        worksheet.write(row, 0, 'Referencia:', info_label_format)
        worksheet.write(row, 1, self.source_move_id.ref or '', info_value_format)
        row += 1
        
        worksheet.write(row, 0, 'Diario:', info_label_format)
        worksheet.write(row, 1, self.source_move_id.journal_id.name, info_value_format)
        row += 2
        
        # Tabla de líneas del asiento
        worksheet.write(row, 0, 'Etiqueta', header_format)
        worksheet.write(row, 1, 'Cuenta', header_format)
        worksheet.write(row, 2, 'Débito', header_format)
        worksheet.write(row, 3, 'Crédito', header_format)
        worksheet.write(row, 4, 'Factura Identificada', header_format)
        row += 1
        
        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 50)  # Etiqueta
        worksheet.set_column(1, 1, 25)  # Cuenta
        worksheet.set_column(2, 2, 15)  # Débito
        worksheet.set_column(3, 3, 15)  # Crédito
        worksheet.set_column(4, 4, 20)  # Factura Identificada
        
        # Escribir líneas del asiento
        for line in self.source_move_id.line_ids:
            if line.account_id == self.discount_account_id:
                worksheet.write(row, 0, line.name or '', text_format)
                worksheet.write(row, 1, f"{line.account_id.code} - {line.account_id.name}", text_format)
                worksheet.write(row, 2, line.debit, number_format)
                worksheet.write(row, 3, line.credit, number_format)
                
                # Identificar factura
                invoice_number = self._extract_invoice_number_from_line(line.name)
                worksheet.write(row, 4, invoice_number or 'No identificada', text_format)
                row += 1

    def action_download_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/conditional.discount.report.wizard/{self.id}/excel_file/{self.excel_filename}?download=true',
            'target': 'self',
        }

    def action_back(self):
        """Volver al estado inicial"""
        self.invoice_line_ids.unlink()
        self.write({
            'state': 'draft', 
            'excel_file': False, 
            'excel_filename': False,
            'records_found': 0,
            'records_excluded': 0
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'conditional.discount.report.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
