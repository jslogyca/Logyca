# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ReportExcelSaleProduct(models.Model):
    _name = "report.excel.sale.product"
    _auto = False
    _description = "Report Sale Product"

    id = fields.Integer('ID')
    partner_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    move_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    vat = fields.Char('Vat')
    invoice_date = fields.Date('Invoice Date')
    invoice_date_due = fields.Date('Invoice Date Due')
    company_id = fields.Many2one('res.company','Compañía')
    invoice_origin = fields.Char('Origin')
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic', readonly=True)
    analytic_account_red = fields.Many2one('account.analytic.account', 'Red', readonly=True)
    analytic_group_id = fields.Many2one('account.analytic.group', 'Group', readonly=True)
    analytic_group_two_id = fields.Many2one('account.analytic.group', 'Group Two', readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                    ('posted', 'Posted'),
                                    ('cancel', 'Cancelled')], string='Status', default='draft')
    vendedor_id = fields.Many2one('res.partner', 'Cliente', readonly=True)
    team_id = fields.Many2one('crm.team', 'Cliente', readonly=True)
    x_send_dian = fields.Boolean('Send DIAN')
    x_date_send_dian = fields.Date('Date Send DIAN')
    x_cufe_dian = fields.Char('CUFE')
    currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
    price_unit_by_product = fields.Float('Price Unit_by Product')
    quantity = fields.Float('Quantity')
    price_unit = fields.Float('Price Unit')
    discount = fields.Float('Discount')
    discount_id = fields.Float('Discount id')
    neto = fields.Float('Neto')
    tax = fields.Float('Tax')
    price_total = fields.Float('Price Total')


    def _select(self):
        select_str = """
        SELECT 
            m.id as id,
            m.id as move_id,
            CASE WHEN p.parent_id IS NULL 
            THEN p.id 
            ELSE pp.id
            END AS partner_id,
            p.vat,
            m.invoice_date AS invoice_date,
            m.invoice_date_due AS invoice_date_due,
            m.invoice_origin AS invoice_origin,
            ppt.id as product_id,
            c.id as company_id,
            cta.id as analytic_account_id,
            ctal.id as analytic_account_red,
            gf.id as analytic_group_id,
            gl.id as analytic_group_two_id,                                    
            CASE WHEN m.state='posted'
            THEN 'Publicada'
            ELSE 'Borrador'
            END AS state,
            pu.id as vendedor_id,
            t.id as team_id,
            m.x_send_dian as x_send_dian,
            m.x_date_send_dian as x_date_send_dian,
            m.x_cufe_dian as x_cufe_dian,
            mc.id as currency_id,
            CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
            THEN (l.price_unit*-1)
            WHEN m.type = 'out_refund' and l.amount_currency<>0.0
            THEN l.debit
            WHEN l.amount_currency<>0.0
            THEN l.credit
            ELSE l.price_unit
            END AS price_unit_by_product,
            l.quantity,   
            CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
            THEN ((l.price_unit*l.quantity)*-1)
            WHEN m.type = 'out_refund' and l.amount_currency<>0.0
            THEN l.debit
            WHEN l.amount_currency<>0.0
            THEN l.credit
            ELSE (l.price_unit*l.quantity)
            END AS price_unit,
            CASE WHEN l.discount>0
            THEN round(((l.price_unit*l.discount)/100),2)
            ELSE 0.0
            END AS discount,
            l.discount as discount_id,
            CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
            THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
            WHEN m.type = 'out_refund' and l.amount_currency<>0.0
            THEN l.debit
            WHEN l.amount_currency<>0.0
            THEN l.credit
            ELSE ((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))
            END AS neto,
            CASE WHEN l.discount=100
            THEN 0.0
            WHEN (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)=0
            THEN 0.0
            WHEN l.amount_currency<>0.0
            THEN l.credit
            WHEN m.type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
            THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
            ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
            END AS tax,
            CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
            THEN (l.price_total*-1)
            WHEN m.type = 'out_refund' and l.amount_currency<>0.0
            THEN l.debit
            WHEN l.amount_currency<>0.0
            THEN l.credit
            ELSE l.price_total
            END AS price_total
		"""
        return select_str


    def _from(self):

        from_str = """
            account_move m
                inner join account_move_line l on m.id=l.move_id
                inner join res_partner p on p.id=m.partner_id
                inner join product_product ppt on ppt.id=l.product_id
                inner join product_template pt on pt.id=ppt.product_tmpl_id
                left join res_partner pp on p.parent_id=pp.id
                inner join res_company c on c.id=m.company_id
                inner join res_users u on u.id=m.invoice_user_id
                inner join res_partner pu on pu.id=u.partner_id
                inner join crm_team t on t.id=m.team_id
                LEFT JOIN account_analytic_account cta on cta.id=m.analytic_account_id
                LEFT JOIN account_analytic_account ctal on ctal.id=l.analytic_account_id      
                LEFT join account_analytic_group gf on gf.id=l.x_account_analytic_group
                LEFT join account_analytic_group gl on gl.id=l.x_account_analytic_group_two
                INNER JOIN res_currency mc on mc.id=m.currency_id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE m.type in ('out_invoice', 'out_refund') and m.state='posted' and exclude_from_invoice_tab is False
                ORDER BY m.id DESC
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