# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    invoice_sell_id = fields.Many2one(string='Invoice Sell', comodel_name='account.move', ondelete='restrict')

    def set_to_close_full(self, invoice_line_id, date=None):
        self.ensure_one()
        disposal_date = date or fields.Date.today()
        if invoice_line_id and self.children_ids.filtered(lambda a: a.state in ('draft', 'open') or a.value_residual > 0):
            raise UserError("You cannot automate the journal entry for an asset that has a running gross increase. Please use 'Dispose' on the increase(s).")
        full_asset = self + self.children_ids
        if invoice_line_id and invoice_line_id.move_id.type=='out_invoice':
            full_asset.write({'state': 'close', 'disposal_date': disposal_date, 'invoice_sell_id': invoice_line_id.move_id.id})
        else:
            full_asset.write({'state': 'close', 'disposal_date': disposal_date})

    @api.onchange('acquisition_date')
    def _onchange_acquisition_date_set_prorata(self):
        self._set_prorate_fields()

    @api.depends('acquisition_date')
    def _compute_prorate_defaults(self):
        for record in self:
            record._set_prorate_fields()

    def _set_prorate_fields(self):
        if self.acquisition_date:
            self.prorata_computation_type = 'constant_periods'
            self.prorata_date = self.acquisition_date.replace(day=1)            
