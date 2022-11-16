# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class ReportExcelEnforcement(models.Model):
    _name = "report.excel.enforcement"
    _auto = False
    _description = "Report Enforcement"

    id = fields.Integer('ID')
    move_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    date = fields.Date('Invoice Date')
    year_fact = fields.Char('Year Fact')
    mes_fact = fields.Char('Mes Fact')
    analytic_group_id = fields.Char('Linea Analitica', readonly=True)
    analytic_group_two_id = fields.Many2one('account.analytic.group', 'Group Two', readonly=True)    
    ref = fields.Char('Ref')
    company_id = fields.Many2one('res.company','Compañía')
    x_studio_clase = fields.Char('Clase')
    cuenta_analitica = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True)
    descripcion = fields.Char('descripcion')
    tipo_cuenta = fields.Char('tipo_Cuenta')
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    quantity = fields.Float('Quantity')
    partner_id = fields.Many2one('res.partner', 'partner', readonly=True)
    importe = fields.Float('importe')
    credit = fields.Float('credit')
    debit = fields.Float('debit')

    def _select(self):
        select_str = """
        SELECT
            a.id as id,
            a.id as move_id,
            coalesce(a.date,'1900-01-01') as date,
            date_part('year',a.date) as year_fact,
            date_part('month',a.date)as mes_fact,
            q.id as analytic_group_id,
            p.id as analytic_group_two_id,
            a.ref as ref,
            j.id as company_id,
            e.x_studio_clase as x_studio_clase,
            d.id  as cuenta_analitica,
            a.name as descripcion, 
            e.code as tipo_cuenta,
            f.id as product_id , 
            b.quantity as quantity, 
            i.id as partner_id,
            coalesce(c.amount,b.balance*-1) as importe, 
            b.credit as credit,
            b.debit as debit
        """
        return select_str

    def _from(self):

        from_str = """
            account_move a
                inner join account_move_line b on a.id = b.move_id
                left join account_analytic_line c on b.id = c.move_id
                left join account_analytic_account d on c.account_id = d.id
                left join account_account e on b.account_id = e.id
                left join product_product f on f.id = b.product_id
                left join product_variant_combination PVC on f.id = PVC.product_product_id
                left join product_template_attribute_value PTAV on PVC.product_template_attribute_value_id = PTAV.id
                left join product_attribute_value PAV on PTAV.product_attribute_value_id = PAV.id
                left join product_template g on g.id = f.product_tmpl_id
                left join uom_uom h on h.id = b.product_uom_id
                left join res_partner i on i.id = b.partner_id
                left join res_company j on j.id = a.company_id
                left join account_analytic_line_tag_rel k on k.line_id  = c.id
                left join account_analytic_tag l on l.id = k.tag_id
                left join logyca_budget_group m on m.id = b.x_budget_group 
                left join res_users n on n.id = b.create_uid 
                left join res_users o on o.id = b.write_uid 
                left join res_partner usu_crea on usu_crea.id = n.partner_id 
                left join res_partner usu_mod on usu_mod.id = o.partner_id
                left join account_analytic_group p on d.group_id = p.id
                left join account_analytic_group q on p.parent_id = q.id
        """

        return from_str

    def _group_by(self):
        group_by_str = """
                WHERE (e.code like '4%' or e.code like '5%' or e.code like '6%') and a.state = 'posted'
                ORDER BY a.id DESC
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