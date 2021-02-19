# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    invoice_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta Red de Valor')

class AccountMove(models.Model):
    _inherit = 'account.move'


    analytic_account_id = fields.Many2one('account.analytic.account', string='Red de Valor')

    """
    This method is overwritten because an error was found in the original code when making a
    credit note of an invoice with deferred income, the error was presented in line 45 when sending the name variable. 
    """
    def _reverse_moves(self, default_values_list=None, cancel=False):
        for move in self:
            # Report the value of this move to the next draft move or create a new one
            if move.asset_id:
                # Set back the amount in the asset as the depreciation is now void
                move.asset_id.value_residual += move.amount_total
                # Recompute the status of the asset for all depreciations posted after the reversed entry
                for later_posted in move.asset_id.depreciation_move_ids.filtered(lambda m: m.date >= move.date and m.state == 'posted'):
                    later_posted.asset_depreciated_value -= move.amount_total
                    later_posted.asset_remaining_value += move.amount_total
                first_draft = min(move.asset_id.depreciation_move_ids.filtered(lambda m: m.state == 'draft'), key=lambda m: m.date, default=None)
                if first_draft:
                    # If there is a draft, simply move/add the depreciation amount here
                    # The depreciated and remaining values don't need to change
                    first_draft.amount_total += move.amount_total
                else:
                    # If there was no draft move left, create one
                    last_date = max(move.asset_id.depreciation_move_ids.mapped('date'))
                    method_period = move.asset_id.method_period

                    self.create(self._prepare_move_for_asset_depreciation({
                        'asset_id': move.asset_id,
                        'move_ref': _('Report of reversal for %s')  % (move.asset_id.name),
                        'amount': move.amount_total,
                        'date': last_date + (relativedelta(months=1) if method_period == "1" else relativedelta(years=1)),
                        'asset_depreciated_value': move.amount_total + max(move.asset_id.depreciation_move_ids.mapped('asset_depreciated_value')),
                        'asset_remaining_value': 0,
                    }))

                msg = _('Depreciation entry %s reversed (%s)') % (move.name, formatLang(self.env, move.amount_total, currency_obj=move.company_id.currency_id))
                move.asset_id.message_post(body=msg)

        return super(AccountMove, self)._reverse_moves(default_values_list, cancel)