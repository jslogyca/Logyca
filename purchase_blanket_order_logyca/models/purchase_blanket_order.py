# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class PurchaseBlanketOrder(models.Model):
    _name = "purchase.blanket.order"
    _inherit = ["purchase.blanket.order", "analytic.mixin"]

    def _get_type_id(self):
        return self.env['purchase.blanket.order.type'].search([], limit=1)

    budget_group_id = fields.Many2one('logyca.budget_group', string='Budget Group', ondelete='restrict')
    type_blanket_id = fields.Many2one('purchase.blanket.order.type', string="Agreement Type", required=True, default=_get_type_id)
    amount_invoice = fields.Monetary(
        string="Total Facturado", store=True, readonly=True, compute="_compute_invoice_all")
    amount_invoice_pend = fields.Monetary(
        string="Total Pendiente", store=True, readonly=True, compute="_compute_invoice_all")
    simulation_text = fields.Html('Detalle de Simulación', compute='_compute_simulation_details')
    simulation_text_iva = fields.Html('Detalle de Simulación', compute='_compute_simulation_detail_iva')
    percent_invoiced = fields.Float(
        string="Porcentaje Facturado (%)",
        compute="_compute_percent_invoiced",
        store=True,
        digits=(16, 2),
    )
    percent_pend_invoiced = fields.Float(
        string="Porcentaje Pendiente (%)",
        compute="_compute_percent_invoiced",
        store=True,
        digits=(16, 2),
    )
    user_approver_id = fields.Many2one(
        "res.users",
        string="Aprobado por",
        readonly=True )
    approver_date = fields.Date('Date Approver', tracking=True)
    total_amount = fields.Boolean(compute='_compute_invoice_all')
    moves_count = fields.Integer(compute="_compute_moves_count")
    months_duration = fields.Integer(
        string='Meses de vigencia',
        compute='_compute_months_duration',
        store=True,
        help='Meses entre fecha de inicio y fecha de vigencia/validez.'
    )
    approval_type = fields.Selection(related='type_blanket_id.approval_type')
    higher_iva = fields.Boolean('Mayor Valor del IVA', default=False)
    higher_iva_tariff = fields.Selection([('5', '5%'), 
                                        ('19', '19%'),
                                        ('0', '0%'), ], string='Tarifa IVA', default='0')
    amount_higher_iva = fields.Monetary(string="Total Pendiente", store=True, readonly=True, compute="_compute_invoice_all")
    type_amount = fields.Selection([('by_contract', 'Por Contracto'), 
                                        ('by_budget', 'Por Presupuesto')], string='Tipo de Cobro', default='by_contract')

    @api.depends('date_start', 'validity_date')
    def _compute_months_duration(self):
        for rec in self:
            rec.months_duration = 0
            if not rec.date_start or not rec.validity_date:
                continue

            # Normalizar a date (opción simple)
            start = fields.Date.to_date(rec.date_start)          # siempre date
            end = fields.Date.to_date(rec.validity_date)         # toma solo la parte de fecha

            # Si prefieres respetar zona horaria del usuario para el Datetime:
            # if isinstance(rec.validity_date, datetime):
            #     end_dt = fields.Datetime.context_timestamp(rec, rec.validity_date)
            #     end = end_dt.date()

            if end < start:
                continue

            rd = relativedelta(end, start)
            months = rd.years * 12 + rd.months
            # Redondear meses parciales hacia arriba (opcional):
            # if rd.days > 0:
            #     months += 1
            rec.months_duration = months 
    
    @api.depends("line_ids.price_total")
    def _compute_invoice_all(self):
        for order in self:
            amount_untaxed = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
            amount_invoice = 0.0
            invoice_ids = order._get_purchase_orders()
            invoice_ids = invoice_ids.filtered(lambda inv: inv.invoice_status == 'invoiced')
            amount_invoice = sum(invoice.amount_untaxed or 0.0 for invoice in invoice_ids)
            amount_invoice_pend = amount_untaxed - amount_invoice
            if order.higher_iva and order.higher_iva_tariff:
                if order.higher_iva_tariff == '5':
                    amount_higher_iva = ((amount_untaxed)*5)/100
                elif order.higher_iva_tariff == '19':
                    amount_higher_iva = ((amount_untaxed)*19)/100
                else:
                    amount_higher_iva = 0.0
            else:
                amount_higher_iva = 0.0
            amount_untaxed = amount_untaxed + amount_higher_iva
            if order.amount_untaxed:
                percent_invoiced = (order.amount_invoice / amount_untaxed) * 100
                percent_pend_invoiced = (order.amount_invoice_pend / amount_untaxed) * 100                
            else:
                percent_invoiced = 0.0
                percent_pend_invoiced = 0.0

            order.update(
                {
                    "amount_invoice": amount_invoice,
                    "amount_invoice_pend": amount_invoice_pend,
                    "amount_higher_iva": amount_higher_iva,
                    "amount_untaxed": amount_untaxed,
                    "total_amount": True,
                    "percent_invoiced": percent_invoiced,
                    "percent_pend_invoiced": percent_pend_invoiced,
                }
            )    

    @api.depends('amount_untaxed', 'amount_invoice')
    def _compute_percent_invoiced(self):
        for record in self:
            if record.amount_untaxed:
                record.percent_invoiced = (record.amount_invoice / record.amount_untaxed) * 100
                record.percent_pend_invoiced = (record.amount_invoice_pend / record.amount_untaxed) * 100                
            else:
                record.percent_invoiced = 0.0
                record.percent_pend_invoiced = 0.0
            if record.budget_group_id:
                record.analytic_distribution = record.budget_group_id.analytic_distribution
            else:
                record.analytic_distribution = False                

    @api.onchange('budget_group_id')
    def onchange_budget_group(self):
        if self.budget_group_id:
            self.analytic_distribution = self.budget_group_id.analytic_distribution
        else:
            self.analytic_distribution = False

    @api.depends('amount_invoice', 'amount_untaxed')
    def _compute_simulation_details(self):
        for record in self:
            simulation_text = record._generate_simulation_text()
            record.simulation_text = simulation_text

    @api.depends('higher_iva', 'higher_iva_tariff', 'amount_higher_iva', 'amount_invoice', 'amount_untaxed')
    def _compute_simulation_detail_iva(self):
        for record in self:
            simulation_text_iva = record._generate_simulation_text_iva()
            record.simulation_text_iva = simulation_text_iva

    def _generate_simulation_text_iva(self):
        """Genera el texto detallado de la simulación enfocado en valores IVA"""
        self.ensure_one()
        amount_higher_iva = self.amount_higher_iva

        return f"""
        <div style="font-family: system-ui; max-width: 800px; line-height: 1.6;">
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div style="flex: 1; padding: 15px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">
                    <div style="font-size: 0.9em; color: #6c757d;">Mayor valor del IVA</div>
                    <div style="font-size: 1.4em; font-weight: bold; color: #212529; margin: 8px 0;">
                        ${self.amount_higher_iva:,.2f}
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_simulation_text(self):
        """Genera el texto detallado de la simulación enfocado en valores"""
        self.ensure_one()
        amount_invoice = self.amount_untaxed

        return f"""
        <div style="font-family: system-ui; max-width: 800px; line-height: 1.6;">
            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                <div style="flex: 1; padding: 15px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">
                    <div style="font-size: 0.9em; color: #6c757d;">Total del Contrato</div>
                    <div style="font-size: 1.4em; font-weight: bold; color: #212529; margin: 8px 0;">
                        ${self.amount_untaxed:,.2f}
                    </div>
                    <div style="font-size: 0.8em; color: #6c757d;">
                        {self.name == '15' and '100%' or self.name == '0' and '50%' or 'No aplica'}
                    </div>
                </div>
                <div style="flex: 1; padding: 15px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">
                    <div style="font-size: 0.9em; color: #6c757d;">Facturado</div>
                    <div style="font-size: 1.4em; font-weight: bold; color: #212529; margin: 8px 0;">
                        ${self.amount_invoice:,.2f}
                    </div>
                    <div style="font-size: 0.8em; color: #6c757d;">
                        {self.percent_invoiced} {'%'}
                    </div>
                </div>
                <div style="flex: 1; padding: 15px; background-color: #f8f9fa; border-radius: 4px; border: 1px solid #dee2e6;">
                    <div style="font-size: 0.9em; color: #6c757d;">Pendiente por Facturar</div>
                    <div style="font-size: 1.4em; font-weight: bold; color: #212529; margin: 8px 0;">
                        ${self.amount_invoice_pend:,.2f}
                    </div>
                    <div style="font-size: 0.8em; color: #6c757d;">
                        {self.percent_pend_invoiced} {'%'}
                    </div>
                </div>
            </div>
        </div>
        """

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            vals = {"user_approver_id": self.env.uid, "approver_date": fields.Date.today()}
            order.write(vals)
        return res

    def action_view_moves(self):
        purchase_orders = self._get_purchase_moves()
        action = self.env['ir.actions.actions']._for_xml_id('account.action_move_in_invoice_type')
        if len(purchase_orders) > 0:
            action["domain"] = [("id", "in", purchase_orders.ids)]
            action["context"] = [("id", "in", purchase_orders.ids)]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def _get_purchase_moves(self):
        return self.mapped("line_ids.purchase_lines.invoice_lines.move_id")

    def _compute_moves_count(self):
        for blanket_order in self:
            blanket_order.moves_count = len(blanket_order._get_purchase_moves())
