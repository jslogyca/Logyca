# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ReportDiffMoveLine(models.Model):
    _name = "report.diff.move.line"
    _auto = False
    _description = "Diferencia en Cambio"

    id = fields.Integer('ID')
    move_id = fields.Many2one('account.move', 'Asiento', readonly=True)
    line_id = fields.Many2one('account.move.line', 'Apunte', readonly=True)
    account_id = fields.Many2one('account.account', 'Cuenta', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Asociado', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True)    
    amount_currency = fields.Float(string='Importe en divisa')
    amount_currency_currency = fields.Float(string='Importe en divisa')
    balance = fields.Float(string='Balance')
    date = fields.Date('Fecha')

    def _select(self):
        select_str = """
            select 
            l.id as id,
            l.move_id as move_id,
            l.id as line_id,
            l.account_id as account_id,
            l.amount_currency as amount_currency,
            CASE 
                WHEN l.currency_id != c.currency_id THEN l.amount_currency
                ELSE 0
            END as amount_currency_currency,
            l.balance as balance,
            l.date as date,
            l.company_id as company_id,
            l.partner_id as partner_id,
            l.currency_id as currency_id
		"""
        return select_str


    def _from(self):

        from_str = """
            account_move_line l
            LEFT JOIN res_company c ON l.company_id = c.id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE parent_state='posted'
                ORDER BY l.id DESC
        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (
            %s
            FROM  %s 
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by())

        # _logger.info(sql)
        print('SQL', sql)
        self.env.cr.execute(sql)