# -*- coding: utf-8 -*-

from collections import defaultdict
from odoo import api, fields, models, Command, _
from odoo.exceptions import UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    credit_card_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor de la Tarjeta de Crédito',
        tracking=True,
        help='Proveedor al que va la factura de la tarjeta de crédito',
    )
    
    credit_card_id = fields.Many2one(
        comodel_name='credit.card',
        string='Tarjeta de Crédito',
        tracking=True,
        help='Tarjeta de crédito corporativa utilizada para los gastos'
    )

    @api.depends('expense_line_ids.payment_mode')
    def _compute_payment_mode(self):
        """Override para asegurar que el payment_mode se calcula correctamente"""
        return super()._compute_payment_mode()
    
    @api.onchange('credit_card_id')
    def _onchange_credit_card_id(self):
        """Auto-completar el proveedor de la tarjeta cuando se selecciona una tarjeta"""
        if self.credit_card_id:
            self.credit_card_partner_id = self.credit_card_id.partner_id

    def _prepare_expense_credit_card_move_vals(self):
        """
        Prepara los valores para el asiento contable cuando el pago es con tarjeta de crédito.
        Crea un asiento con:
        - Una línea al débito por cada gasto con su cuenta y proveedor
        - Una línea al crédito CXP por cada gasto con la cuenta de la tarjeta y el tercero de la tarjeta
        """
        self.ensure_one()

        # Verificar que todos los gastos sean de tarjeta de crédito
        non_credit_card = self.expense_line_ids.filtered(lambda e: e.payment_mode != 'credit_card')
        if non_credit_card:
            return False

        if not self.credit_card_id:
            raise UserError(_('Debe seleccionar la tarjeta de crédito.'))

        if not self.journal_id:
            raise UserError(_('Debe seleccionar un diario contable.'))

        move_lines = []

        # Procesar cada gasto
        for expense in self.expense_line_ids:
            if not expense.partner_id:
                raise UserError(_(
                    'El gasto "%s" no tiene un proveedor asignado. '
                    'Por favor asigne un proveedor a todos los gastos.'
                ) % expense.name)

            if not expense.account_id:
                raise UserError(_(
                    'El gasto "%s" no tiene una cuenta contable asignada. '
                    'Por favor configure la cuenta en la categoría del gasto.'
                ) % expense.name)

            # Calcular el monto base del gasto (sin incluir valor excluido del IVA)
            base_amount = expense.quantity * (expense.total_amount)
            
            # Línea de débito para el gasto base
            debit_line_vals = {
                'name': expense.name,
                'account_id': expense.account_id.id,
                'partner_id': expense.partner_id.id,
                'debit': base_amount if base_amount > 0 else 0.0,
                'credit': abs(base_amount) if base_amount < 0 else 0.0,
                'quantity': expense.quantity,
                'product_id': expense.product_id.id if expense.product_id else False,
                'product_uom_id': expense.product_uom_id.id if expense.product_uom_id else False,
                'analytic_distribution': expense.analytic_distribution,
            }
            move_lines.append(Command.create(debit_line_vals))
            
            # Inicializar el monto total con la base
            expense_amount = base_amount

            # Procesar impuestos si existen (sobre la base, sin el valor excluido)
            if expense.tax_ids:
                taxes = expense.tax_ids.compute_all(
                    expense.total_amount,  # Solo sobre el precio unitario
                    currency=expense.currency_id,
                    quantity=expense.quantity,
                    product=expense.product_id,
                    partner=expense.partner_id
                )

                # Agregar líneas de impuestos
                for tax in taxes['taxes']:
                    tax_amount = tax['amount']
                    tax_record = self.env['account.tax'].browse(tax['id'])
                    
                    if tax_amount != 0:
                        # Obtener la cuenta del impuesto
                        tax_repartition_lines = tax_record.invoice_repartition_line_ids.filtered(
                            lambda x: x.repartition_type == 'tax'
                        )
                        tax_account = tax_repartition_lines[0].account_id if tax_repartition_lines and tax_repartition_lines[0].account_id else expense.account_id
                        
                        tax_line_vals = {
                            'name': tax_record.name,
                            'account_id': tax_account.id,
                            'partner_id': expense.partner_id.id,
                            'debit': tax_amount if tax_amount > 0 else 0.0,
                            'credit': abs(tax_amount) if tax_amount < 0 else 0.0,
                            'tax_line_id': tax_record.id,
                        }
                        move_lines.append(Command.create(tax_line_vals))
                        expense_amount += tax_amount
            
            # Agregar línea de débito para el valor excluido del IVA (si existe)
            if expense.amount_tax_excluded > 0:
                excluded_description = expense.amount_tax_excluded_description or 'Valor excluido del IVA'
                excluded_line_vals = {
                    'name': f"{expense.name} - {excluded_description}",
                    'account_id': expense.account_id.id,
                    'partner_id': expense.partner_id.id,
                    'debit': expense.amount_tax_excluded if expense.amount_tax_excluded > 0 else 0.0,
                    'credit': abs(expense.amount_tax_excluded) if expense.amount_tax_excluded < 0 else 0.0,
                    'analytic_distribution': expense.analytic_distribution,
                }
                move_lines.append(Command.create(excluded_line_vals))
                expense_amount += expense.amount_tax_excluded

            # Línea de crédito CXP para cada gasto con la cuenta y tercero de la tarjeta
            # Usar el total que incluye el valor excluido
            credit_line_vals = {
                'name': _('CXP Tarjeta - %s') % expense.name,
                'account_id': self.credit_card_id.account_id.id,
                'partner_id': self.credit_card_id.partner_id.id,
                'debit': abs(expense_amount) if expense_amount < 0 else 0.0,
                'credit': expense_amount if expense_amount > 0 else 0.0,
            }
            move_lines.append(Command.create(credit_line_vals))

        # Preparar valores del asiento contable
        move_vals = {
            'journal_id': self.journal_id.id,
            'date': self.accounting_date or fields.Date.context_today(self),
            'ref': self.name,
            'line_ids': move_lines,
            'currency_id': self.currency_id.id,
        }

        return move_vals

    def action_sheet_move_create(self):
        """
        Override del método que crea el asiento contable.
        Si el pago es con tarjeta de crédito, usa nuestra lógica personalizada.
        """
        # Filtrar los sheets que son de tarjeta de crédito
        # (todos los gastos deben ser credit_card)
        credit_card_sheets = self.filtered(
            lambda sheet: all(
                expense.payment_mode == 'credit_card' 
                for expense in sheet.expense_line_ids
            ) and sheet.credit_card_id
        )
        other_sheets = self - credit_card_sheets

        # Procesar los sheets con tarjeta de crédito
        for sheet in credit_card_sheets:
            move_vals = sheet._prepare_expense_credit_card_move_vals()
            if move_vals:
                move = self.env['account.move'].create(move_vals)
                sheet.write({'account_move_ids': [Command.link(move.id)]})
                move.action_post()

        # Procesar el resto con la lógica estándar
        if other_sheets:
            return super(HrExpenseSheet, other_sheets).action_sheet_move_create()

        return True
    
    def action_view_account_moves(self):
        """Acción para ver los asientos contables generados"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_journal_line')
        
        if len(self.account_move_ids) > 1:
            action['domain'] = [('id', 'in', self.account_move_ids.ids)]
        elif self.account_move_ids:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state, view) for state, view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = self.account_move_ids.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action
