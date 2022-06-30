# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class AccountDebtorsReport(models.Model):
    _name = "account.debtors.report"
    _auto = False
    _description = "Account Debtors Report"

    id = fields.Integer('ID')
    date = fields.Date('Date')
    year_fact = fields.Char('Year Fact')
    move_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    vat = fields.Char('Vat')
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    product_template_id = fields.Many2one('product.template', 'Product', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    amount_untaxed = fields.Float('Amount Untaxed')
    amount_tax = fields.Float('Tax')
    amount_total = fields.Float('Total')
    amount_residual = fields.Float(' Residual')
    invoice_date_due = fields.Date('Invoice Date Due')
    payment_term_id = fields.Many2one('account.payment.term','Payment Term')
    days_debtor = fields.Float('Days Debtor')
    mes_fact = fields.Char('Mes Fact')
    type_debtors = fields.Char('Type Debtors')
    vendedor_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    team_id = fields.Many2one('crm.team', 'Cliente', readonly=True)
    x_debt_portfolio_monitoring = fields.Text('Seg Debtors')
    x_last_contact_debtor = fields.Date('Last Contact Debtor')
    x_estimated_payment_date = fields.Date('Estimated Payment Date')
    x_debtor_portfolio_status_id = fields.Many2one('debtor.portfolio.status', 'Status', readonly=True)
    company_id = fields.Many2one('res.company','Compañía')

    def _select(self):
        select_str = """
        SELECT  to_char(am.date,'YYYY/MM/DD') as date,
            LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4) AS year_fact,
            am.id AS id, 
            am.id AS move_id, 
            am.company_id AS company_id, 
            rp.vat AS vat,
            CASE WHEN rp.parent_id IS NULL 
            THEN rp.id 
            ELSE rpp.id
            END AS partner_id,
            pt.id AS product_template_id,
            pp.id AS product_id,
            am.amount_untaxed as amount_untaxed,
            am.amount_tax AS amount_tax,
            am.amount_total AS amount_total,
            am.amount_residual AS amount_residual,
            to_char(am.invoice_date_due,'YYYY/MM/DD') AS invoice_date_due,
            apt.id AS payment_term_id,
            CASE WHEN now() > am.invoice_date_due THEN DATE_PART('day', now() - am.invoice_date_due) ELSE 0 END AS days_debtor,
            SUBSTRING(TO_CHAR(am.invoice_date_due,'YYYY-MM-DD'),6,2) AS mes_fact,
            CASE WHEN now() > am.invoice_date_due then 'VENCIDA ' || LEFT(TO_CHAR(am.date, 'YYYY-MM-DD'),4)  else 'NO VENCIDA' END AS type_debtors,
            rppp.id AS vendedor_id,
            t.id AS team_id,
            am.x_debt_portfolio_monitoring AS x_debt_portfolio_monitoring,
            to_char(am.x_last_contact_debtor,'YYYY/MM/DD') AS x_last_contact_debtor,
            dps.id AS x_debtor_portfolio_status_id,
            to_char(am.x_estimated_payment_date,'YYYY/MM/DD') AS x_estimated_payment_date
		"""
        return select_str


    def _from(self):

        from_str = """
            account_move am
                LEFT JOIN account_analytic_account aaa ON aaa.id = am.analytic_account_id 
                INNER JOIN account_payment_term apt on apt.id = am.invoice_payment_term_id
                inner join crm_team t on t.id=am.team_id
                LEFT JOIN debtor_portfolio_status dps on dps.id=am.x_debtor_portfolio_status_id
                LEFT JOIN res_partner rp ON rp.id = am.partner_id
                LEFT JOIN res_partner rpp ON rpp.id = rp.parent_id
                LEFT JOIN res_users ru ON ru.id = am.invoice_user_id
                LEFT JOIN res_partner rppp ON ru.partner_id = rppp.id
                INNER JOIN account_move_line aml ON am.id = aml.move_id
                INNER JOIN product_product pp ON aml.product_id= pp.id
                INNER JOIN product_template pt ON pp.product_tmpl_id = pt.id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
            WHERE
                am.state='posted' 
                and am.type='out_invoice'
                and (am.invoice_payment_state='not_paid' or am.invoice_payment_state='in_payment')
                and (am.name LIKE 'FEC%' or am.name LIKE 'FAC%' or am.name LIKE 'FAM%')
                ORDER BY move_id ASC
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