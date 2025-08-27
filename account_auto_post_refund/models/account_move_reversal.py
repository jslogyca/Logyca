# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def reverse_moves(self):
        """
        Extiende el asistente para crear NC, publicarlas y conciliarlas automáticamente
        con la factura origen. Devuelve una acción mostrando las NC creadas.
        """
        self.ensure_one()
        default_values_list = []
        for move in self.move_ids:
            default_values = {
                'ref': 'Reversión de: ' + move.name or '',
                'date': self.date or fields.Date.context_today(self),
                'journal_id': self.journal_id.id or move.journal_id.id,
            }
            default_values_list.append(default_values)

        refunds = self.move_ids._reverse_moves(default_values_list=default_values_list, cancel=False)
        refunds = refunds.filtered(lambda m: m.move_type in ('out_refund', 'in_refund'))

        if refunds:
            refunds.action_post()

        for refund in refunds:
            origin = refund.reversed_entry_id
            if not origin or origin.state != 'posted':
                continue

            lines = (origin.line_ids | refund.line_ids).filtered(
                lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable') and not l.reconciled
            )

            for account in lines.mapped('account_id'):
                acc_lines = lines.filtered(lambda l, a=account: l.account_id == a)
                for partner in acc_lines.mapped('partner_id'):
                    to_rec = acc_lines.filtered(lambda l, p=partner: l.partner_id == p)
                    if len(to_rec) >= 2:
                        try:
                            to_rec.reconcile()
                        except Exception:
                            pass

        action = {
            'name': _('Credit Notes'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form,tree',
            'domain': [('id', 'in', refunds.ids)],
        }
        # return action