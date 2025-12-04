# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    agrupar_por_factura = fields.Boolean(
        string='Agrupar por Factura',
        default=False,
        help='Si está activado, al contabilizar el gasto se generará una sola CXP al tercero '
             'de la tarjeta de crédito. Si está desactivado, se generará una CXP por cada gasto.'
    )

    def action_submit_sheet(self):
        """Acción para enviar a aprobar el reporte de gastos"""
        self.write({'approval_state': 'submit'})
        return True

    def action_submit_sheets_batch(self):
        """Acción para enviar a aprobar múltiples reportes de gastos"""
        for sheet in self:
            if sheet.state == 'draft':
                sheet.action_submit_sheet()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reportes Enviados'),
                'message': _('%s reporte(s) de gastos enviado(s) a aprobación.') % len(self),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_sheet_move_create(self):
        """
        Override del método para implementar la lógica de agrupación por factura
        Si agrupar_por_factura está activado y hay tarjeta de crédito,
        se genera una sola CXP al tercero de la tarjeta.
        """
        # 1. Llamar al método padre para crear el movimiento contable base
        res = super(HrExpenseSheet, self).action_sheet_move_create()

        # 2. Verificar condiciones: parámetro activo, tarjeta de crédito y partner configurado
        if self.agrupar_por_factura and self.credit_card_id and self.credit_card_id.partner_id:
            print('///////', 'agrupar')
            # Obtener el último asiento creado
            if self.account_move_ids:
                move = self.account_move_ids[-1]

                # Si el asiento está publicado, lo pasamos a borrador para poder editarlo
                was_posted = False
                if move.state == 'posted':
                    move.button_draft()
                    was_posted = True

                # Filtrar líneas de cuenta por pagar (liability_payable) con crédito
                # payable_lines = move.line_ids.filtered(
                #     lambda l: l.account_id.account_type == 'liability_payable' and l.credit > 0
                # )
                payable_lines = move.line_ids.filtered(
                    lambda l: l.account_id.account_type in ('liability_payable','liability_credit_card', 'liability_current', 'liability_non_current') and l.credit > 0
                )                

                if len(payable_lines) > 1:
                    # Calcular totales (Crédito y Moneda extranjera si aplica)
                    total_credit = sum(payable_lines.mapped('credit'))
                    total_amount_currency = sum(payable_lines.mapped('amount_currency'))
                    
                    first_line = payable_lines[0]
                    lines_to_remove = payable_lines[1:]

                    # IMPORTANTE: Usamos check_move_validity=False para evitar el error
                    # de "Asiento descuadrado" durante la manipulación
                    
                    # 1. Eliminar las líneas sobrantes (sin validar cuadre aún)
                    lines_to_remove.with_context(check_move_validity=False).unlink()
                    
                    # 2. Actualizar la primera línea con el total (sin validar cuadre aún)
                    first_line.with_context(check_move_validity=False).write({
                        'credit': total_credit,
                        'amount_currency': total_amount_currency, # Importante sumar esto también
                        'partner_id': self.credit_card_id.partner_id.id,
                        'name': _('Gastos agrupados - %s') % self.name,
                    })

                    # Una vez terminada la manipulación, si estaba publicado, lo volvemos a publicar.
                    # Al publicar, Odoo verificará que el asiento esté cuadrado.
                    if was_posted:
                        move.action_post()
        
        return res

    # def action_sheet_move_create(self):
    #     """
    #     Override del método para implementar la lógica de agrupación por factura
    #     Si agrupar_por_factura está activado y hay tarjeta de crédito,
    #     se genera una sola CXP al tercero de la tarjeta
    #     """
    #     # Para sheets con agrupar_por_factura = True y con tarjeta de crédito
    #     if self.agrupar_por_factura and self.credit_card_id and self.credit_card_id.partner_id:
    #         print('///////', 'agrupar')
    #         # Llamar al método padre para crear el movimiento contable base
    #         res = super(HrExpenseSheet, self).action_sheet_move_create()
            
    #         # Obtener el asiento contable creado
    #         if self.account_move_ids:
    #             move = self.account_move_ids[-1]  # El último asiento creado
                
    #             # Agrupar las líneas de CXP (account payable)
    #             payable_lines = move.line_ids.filtered(
    #                 lambda l: l.account_id.account_type in ('liability_payable','liability_credit_card', 'liability_current', 'liability_non_current') and l.credit > 0
    #             )
    #             print('///////', 'agrupar', payable_lines)
    #             if len(payable_lines) > 1:
    #                 # Calcular el total de crédito
    #                 total_credit = sum(payable_lines.mapped('credit'))
                    
    #                 # Mantener solo la primera línea y actualizar su monto
    #                 first_line = payable_lines[0]
    #                 lines_to_remove = payable_lines[1:]
                    
    #                 # Actualizar la primera línea con el total y el partner de la tarjeta
    #                 first_line.write({
    #                     'credit': total_credit,
    #                     'partner_id': self.credit_card_id.partner_id.id,
    #                     'name': _('Gastos agrupados - %s') % self.name,
    #                 })
                    
    #                 # Eliminar las otras líneas de CXP
    #                 print('///////', 'agrupar', lines_to_remove, total_credit)
    #                 lines_to_remove.unlink()
            
    #         return res
    #     else:
    #         print('/////// sin agrupar')
    #         # Comportamiento normal: una CXP por gasto
    #         return super(HrExpenseSheet, self).action_sheet_move_create()
