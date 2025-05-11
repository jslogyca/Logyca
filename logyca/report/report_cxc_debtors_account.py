# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ReportCXCDebtorsAccount(models.Model):
    _name = "report.cxc.debtors.account"
    _auto = False
    _description = "Report CXC Debtors Account"

    id = fields.Integer('ID')
    company_id = fields.Many2one('res.company','COMPAÑÍA')
    date = fields.Date('FECHA')
    year_fact = fields.Char('AÑO')
    doc_move = fields.Char('DOC')
    number_move = fields.Char('NRO')
    vat = fields.Char('NIT')
    partner_id = fields.Many2one('res.partner', 'RAZÓN SOCIAL', readonly=True)
    move_id = fields.Many2one('account.move', 'FACTURA', readonly=True)
    product_template_id = fields.Many2one('product.template', 'PRODUCTO', readonly=True)
    product_id = fields.Many2one('product.product', 'PRODUCTO', readonly=True)
    amount_untaxed = fields.Float('VALOR')
    amount_tax = fields.Float('T. IVA')
    amount_total = fields.Float('T. FACTURA')
    amount_residual = fields.Float('SALDO FACTURA')
    currency_id = fields.Many2one('res.currency','MONEDA')
    invoice_date_due = fields.Date('FECHA VENCIMIENTO')
    payment_term_id = fields.Many2one('account.payment.term','ACUERDO DE PAGO')
    days_debtor = fields.Float('DÍAS CARTERA VENCIDA')
    mes_fact = fields.Char('MES VENCIMIENTO')
    type_debtors = fields.Char('TIPO CARTERA')
    vendedor_id = fields.Many2one('res.partner', 'RESPONSABLE', readonly=True)
    team_id = fields.Many2one('crm.team', 'EQUIPO DE VENTA', readonly=True)
    x_debt_portfolio_monitoring = fields.Text('SEGUIMIENTO DE CARTERA')
    x_last_contact_debtor = fields.Date('FECHA DE SEGUIMIENTO ULTIMO CONTACTO')
    x_estimated_payment_date = fields.Date('FECHA PROGRAMACIÓN PAGO')
    # x_debtor_portfolio_status_id = fields.Many2one('debtor.portfolio.status', 'ESTADO DE CARTERA', readonly=True)
    x_debtor_portfolio_status_id = fields.Char('ESTADO')
    priority_cxc = fields.Selection([('baja', 'Baja'), 
                                    ('media', 'Media'),
                                    ('alta', 'Alta')], string='PRIORIDAD')
    
    def _select(self):
        select_str = """
            SELECT cc.id as company_id, 
            am.id AS id, 
            am.id AS move_id, 
            am.date as date,
            LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4) AS year_fact,
            LEFT(am.name,3) AS doc_move, 
            RIGHT(am.name,6) AS number_move,
            rp.vat AS vat,
            CASE WHEN rp.parent_id IS NULL 
            THEN rp.id 
            ELSE rpp.id
            END AS partner_id,
            pp.id AS product_id,
            pt.id AS product_template_id,
            aml.price_subtotal as amount_untaxed,
            (aml.price_total - aml.price_subtotal) AS amount_tax,
            aml.price_total AS amount_total,
            aml.price_total AS amount_residual,
            mc.id AS currency_id,
            am.invoice_date_due AS invoice_date_due,
            apt.id AS payment_term_id,
            CASE WHEN now() > am.invoice_date_due THEN DATE_PART('day', now() - am.invoice_date_due) ELSE 0 END AS days_debtor,
            SUBSTRING(TO_CHAR(am.invoice_date_due,'YYYY-MM-DD'),6,2) AS mes_fact,
            CASE WHEN now() > am.invoice_date_due then 'VENCIDA ' || LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4)  else 'NO VENCIDA' END AS type_debtors,
            rppp.id AS vendedor_id,
            t.id AS team_id,
            CASE WHEN (CASE WHEN now() > am.invoice_date_due 
            THEN DATE_PART('day', now() - am.invoice_date_due)
            ELSE 0 END)<=30
            THEN 'baja'
            WHEN (CASE WHEN now() > am.invoice_date_due 
            THEN DATE_PART('day', now() - am.invoice_date_due)
            ELSE 0 END)>30 and (CASE WHEN now() > am.invoice_date_due 
            THEN DATE_PART('day', now() - am.invoice_date_due)
            ELSE 0 END)<=90
            THEN 'media'
            ELSE 'alta'
            END AS priority_cxc            
		"""
        return select_str


    def _from(self):

        from_str = """
            account_move_line aml
                INNER JOIN account_move am on aml.move_id = am.id
                INNER JOIN res_company cc on cc.id=am.company_id
                LEFT JOIN account_payment_term apt on apt.id = am.invoice_payment_term_id
                LEFT join crm_team t on t.id=am.team_id
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN res_partner rpp ON rpp.id = rp.parent_id
                LEFT JOIN res_users ru ON ru.id = am.invoice_user_id
                LEFT JOIN res_partner rppp ON ru.partner_id = rppp.id
                LEFT JOIN product_product pp ON pp.id=aml.product_id
                LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
                LEFT JOIN res_currency mc on mc.id=aml.currency_id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
            WHERE
                am.state='posted' 
                and am.move_type in ('out_invoice', 'entry')
                and (am.payment_state='not_paid' or am.payment_state='in_payment')
                and (am.name LIKE 'FEC%' or am.name LIKE 'FAC%' or am.name LIKE 'FAM%' or am.name LIKE 'CXC%' or am.name LIKE 'FSIV%')
                ORDER BY number_move ASC
        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by())

        # _logger.info(sql)
        self.env.cr.execute(sql)