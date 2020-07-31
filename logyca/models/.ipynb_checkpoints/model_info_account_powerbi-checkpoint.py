# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from functools import lru_cache

class InfoAccountPowerBI(models.Model):
    _name = "account.info.powerbi"
    _description = "Report - Info Contable Power BI"
    _auto = False
    
    # Compañia
    fecha = fields.Date(string='Fecha', readonly=True)
    descripcion = fields.Char(string='Descripción', readonly=True)
    lineaanalitica = fields.Char(string='Linea Analitica', readonly=True)
    familiaanalitica = fields.Char(string='Familia Analitica', readonly=True)
    cuenta_analitica = fields.Char(string='Cuenta Analitica', readonly=True)
    ref = fields.Char(string='Referencia', readonly=True)
    tipo_cuenta = fields.Char(string='Tipo Cuenta', readonly=True)
    #clase = fields.Char(string='Clase Cuenta', readonly=True)
    grupo_presupuestal = fields.Char(string='Grupo Presupuestal', readonly=True)
    cuenta_financiera = fields.Char(string='Cuenta financiera', readonly=True)
    apunte_contable = fields.Char(string='Apunte Contable', readonly=True)
    producto = fields.Char(string='Producto', readonly=True)
    cantidad = fields.Integer(string='Cantidad', readonly=True)
    unidad = fields.Char(string='Unidad', readonly=True)
    asociado = fields.Char(string='Asociado', readonly=True)
    compañia = fields.Char(string='Compañia', readonly=True)
    importe = fields.Float(string='Importe', readonly=True)
    importe_positivo = fields.Float(string='Importe Positivo', readonly=True)
    categoria = fields.Char(string='Categoria', readonly=True)
    creado = fields.Date(string='Fecha Creado', readonly=True)
    creado_por = fields.Char(string='Creado por', readonly=True)
    modificado = fields.Date(string='Fecha Modificado', readonly=True)
    actualizado_por = fields.Char(string='Modificado por', readonly=True)
    
    @api.model
    def _select(self):
        #coalesce(e."x_studio_clase",'-') as clase,
        return '''
            Select Row_Number() over (order by i.display_name) as ID,
                coalesce(a."date",'1900-01-01') as fecha, 
                coalesce(A."name",'-') as descripcion,
                coalesce(q."name",'-') as lineaanalitica,
                coalesce(p."name",'-') as familiaanalitica,
                coalesce(d.code,'-') ||' / '|| coalesce(d.name,'-')  as cuenta_analitica,
                coalesce(a."ref",'-') as ref,
                coalesce(left(e.code,2),'0')  as tipo_cuenta,
                coalesce(m."name",'-') as grupo_presupuestal,
                coalesce(e.code,'-') ||' / '|| coalesce(e.name,'-') as cuenta_financiera,
                coalesce(b."name",'-') as apunte_contable, 
                coalesce(g.name,'-') as  producto, 
                coalesce(b.quantity,'0') as cantidad, 
                coalesce(h.name,'-') as unidad, 
                coalesce(i.display_name,'-') as asociado,
                coalesce(j."name",'-') as compañia, 
                coalesce(c.amount,b.balance) as importe,
                abs(coalesce(c.amount,b.balance)) as importe_positivo, 
                coalesce(l."name",'-')  as categoria,
                coalesce(b."create_date",'1900-01-01') as creado, 
                coalesce(usu_crea.name,'-') as creado_por,
                coalesce(b.write_date,'1900-01-01') as modificado, 
                coalesce(usu_mod.name,'-') as actualizado_por
            From account_move a
                inner join account_move_line b on a.id = b.move_id
                left join account_analytic_line c on b.id = c.move_id
                left join account_analytic_account d on c.account_id = d.id
                left join account_account e on b.account_id = e.id
                left join product_product f on f.id = b.product_id
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
            Where (e.code like '4%s' or e.code like '5%s' or e.code like '6%s')
        ''' % ('%','%','%')

    def init(self):        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s 
            )
        ''' % (
            self._table, self._select()
        ))

    