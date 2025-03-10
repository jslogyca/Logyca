# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ResMemberProductLogyca(models.Model):
    _name = "res.member.product.logyca"
    _auto = False
    _description = "Res Member Product Logyca"

    id = fields.Integer('ID')
    partner_id = fields.Many2one('res.partner', 'Miembro', readonly=True)
    vat = fields.Char(string='NIT')
    year_fact = fields.Char(string='Año')
    product_id = fields.Char(string='Servicio')
    invoice_user_id = fields.Char(string='Facturado por')
    amount_untaxed = fields.Float('Valor', default=0.0)

    def _select(self):
        select_str = """
        SELECT
            l.partner_id as id,
            l.partner_id as partner_id, 
            p.vat as vat,
            date_part('year',m.date) as year_fact,
            pt.name as product_id,
            up.name as invoice_user_id,
            sum(amount_untaxed) as amount_untaxed
		"""
        return select_str


    def _from(self):

        from_str = """
            account_move_line l
            INNER JOIN account_move m on m.id=l.move_id
            INNER JOIN res_partner p on p.id=l.partner_id
            LEFT JOIN product_product pp on l.product_id=pp.id
            LEFT JOIN product_template pt on pp.product_tmpl_id=pt.id
            INNER JOIN res_users u on u.id=m.invoice_user_id
            INNER JOIN res_partner up on up.id=u.partner_id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE l.exclude_from_invoice_tab IS False
                AND m.move_type='out_invoice'
                AND m.date between '2024-01-01' and '2025-12-31'
                AND m.state='posted'
                AND m.payment_state='paid'
                GROUP BY l.partner_id, p.vat, date_part('year',m.date), pt.name, up.name
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