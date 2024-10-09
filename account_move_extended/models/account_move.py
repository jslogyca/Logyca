# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'


    invoice_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta Red de Valor')
    inter_company = fields.Boolean('Intercompany', related='product_id.product_tmpl_id.inter_company', readonly=True, store=True)

    @api.onchange('x_budget_group')
    def onchange_budget_group(self):
        if self.move_id.move_type== 'in_invoice' or self.move_id.move_type== 'in_refund': 
            company_id = self.product_id.company_id.id

            if company_id and company_id == 1:
                #servicios 1
                if self.x_budget_group.lser_analytic_tag_ids:
                    self.analytic_tag_ids = [(6,0, self.x_budget_group.lser_analytic_tag_ids.ids)]
                    self.invoice_tag_ids = False
                elif self.x_budget_group.invoice_tag_ids:
                    self.invoice_tag_ids = self.x_budget_group.invoice_tag_ids.id
                    self.analytic_tag_ids = [(5,0,0)]
                else:
                    self.analytic_tag_ids = [(5,0,0)]
                    self.invoice_tag_ids = False
            elif company_id and company_id == 2:
                #asociación  2
                if self.x_budget_group.iac_analytic_tag_ids:
                    self.analytic_tag_ids = [(6,0, self.x_budget_group.iac_analytic_tag_ids.ids)]
                    self.invoice_tag_ids = False
                elif self.x_budget_group.iac_invoice_tag_ids:
                    self.invoice_tag_ids = self.x_budget_group.iac_invoice_tag_ids.id
                    self.analytic_tag_ids = [(5,0,0)]
                else:
                    self.analytic_tag_ids = [(5,0,0)]
                    self.invoice_tag_ids = False
            elif company_id and company_id == 3:
                #investigación 3
                if self.x_budget_group.log_analytic_tag_ids:
                    self.analytic_tag_ids = [(6,0, self.x_budget_group.log_analytic_tag_ids.ids)]
                    self.invoice_tag_ids = False
                elif self.x_budget_group.log_invoice_tag_ids:
                    self.invoice_tag_ids = self.x_budget_group.log_invoice_tag_ids.id
                    self.analytic_tag_ids = [(5,0,0)]
                else:
                    self.analytic_tag_ids = [(5,0,0)]
                    self.invoice_tag_ids = False

class AccountMove(models.Model):
    _inherit = 'account.move'

    x_debt_portfolio_monitoring = fields.Text('Seguimiento Cartera')
    x_last_contact_debtor = fields.Date('Fecha Último Contacto', help="La fecha en la que nos contactamos por última vez con el deudor")
    x_debtor_portfolio_status_id = fields.Many2one('debtor.portfolio.status', string="Estado Cartera")
    x_debtor_portfolio_status_str = fields.Char(compute="debtor_portfolio_status_as_char", string="Estado Cartera")
    x_estimated_payment_date = fields.Date('Fecha Estimada Pago')
    x_payment_portal_theme = fields.Selection([('logyca', 'LOGYCA'), ('gs1', 'GS1')], string='Portal de Pagos',help="Indica en qué portal de pagos debe pagarse la factura")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Red de Valor')
    reviewed_by = fields.Many2one('res.users', string='Revisado Por', help="Este campo aparece en el reporte de Soporte de Factura", default=False)

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        for m in self:
            journal_type = m.invoice_filter_type_domain or 'general'
            company_id = m.company_id.id or self.env.company.id
            # domain = [('company_id', '=', company_id), ('type', '=', journal_type)]
            domain = [('company_id', '=', company_id)]
            m.suitable_journal_ids = self.env['account.journal'].search(domain)

    @api.depends('x_debtor_portfolio_status_id')
    def debtor_portfolio_status_as_char(self):
        for rec in self:
            rec.x_debtor_portfolio_status_str = rec.x_debtor_portfolio_status_id.name

    @api.onchange('x_debtor_portfolio_status_id')
    def onchange_debtor_portfolio_status(self):
        if self.x_debtor_portfolio_status_str != 'Programación de Pago':
            self.x_estimated_payment_date = None

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

    def action_reviewed_by(self):
        self.reviewed_by = self.env.user
