# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import xlsxwriter
from io import BytesIO
from datetime import datetime


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

    def action_generate_report(self):
        self.ensure_one()
        
        # Buscar apuntes que cumplan los criterios
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('account_id.code', '=', '530535'),
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
            })
        
        if not report_data:
            raise UserError(
                _('No se encontraron registros conciliados con facturas de venta.')
            )
        
        # Generar Excel
        excel_file = self._generate_excel(report_data)
        
        # Actualizar wizard con el archivo
        filename = f'Descuentos_Condicionados_{self.year}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
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
            'context': {
                'default_state': 'done',
                'records_found': len(report_data),
                'records_excluded': excluded_count,
            }
        }

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
        """
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Descuentos Condicionados')
        
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
            'Valor Descuento'
        ]
        
        # Escribir encabezados
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Ajustar ancho de columnas
        worksheet.set_column(0, 0, 18)  # Factura de Venta
        worksheet.set_column(1, 1, 14)  # Fecha Factura
        worksheet.set_column(2, 2, 30)  # Cliente
        worksheet.set_column(3, 3, 15)  # NIT Cliente
        worksheet.set_column(4, 4, 12)  # Moneda Factura
        worksheet.set_column(5, 5, 16)  # Subtotal Factura
        worksheet.set_column(6, 6, 16)  # Total Factura
        worksheet.set_column(7, 7, 20)  # Total Factura (Moneda Cía)
        worksheet.set_column(8, 8, 18)  # Comprobante Pago
        worksheet.set_column(9, 9, 14)  # Fecha Pago
        worksheet.set_column(10, 10, 16)  # Valor Descuento
        
        # Escribir datos
        row = 1
        for record in data:
            worksheet.write(row, 0, record['invoice_number'], text_format)
            
            if record['invoice_date']:
                if isinstance(record['invoice_date'], str):
                    invoice_date = datetime.strptime(record['invoice_date'], '%Y-%m-%d')
                else:
                    invoice_date = record['invoice_date']
                worksheet.write_datetime(row, 1, invoice_date, date_format)
            else:
                worksheet.write(row, 1, '', text_format)
            
            worksheet.write(row, 2, record['partner_name'], text_format)
            worksheet.write(row, 3, record['partner_vat'], text_format)
            worksheet.write(row, 4, record['currency'], text_format)
            worksheet.write(row, 5, record['factura_total_moneda'], number_format)
            worksheet.write(row, 6, record['factura_total'], number_format)
            worksheet.write(row, 7, record['factura_total_compania'], number_format)
            worksheet.write(row, 8, record['pay_move_name'], text_format)
            
            if record['pay_move_date']:
                if isinstance(record['pay_move_date'], str):
                    pay_date = datetime.strptime(record['pay_move_date'], '%Y-%m-%d')
                else:
                    pay_date = record['pay_move_date']
                worksheet.write_datetime(row, 9, pay_date, date_format)
            else:
                worksheet.write(row, 9, '', text_format)
            
            worksheet.write(row, 10, record['valor_530535_debito'], number_format)
            
            row += 1
        
        workbook.close()
        output.seek(0)
        return output.read()

    def action_download_excel(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/conditional.discount.report.wizard/{self.id}/excel_file/{self.excel_filename}?download=true',
            'target': 'self',
        }

    def action_back(self):
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
