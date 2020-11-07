# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from functools import lru_cache

class InfoPartnerPowerBI(models.Model):
    _name = "accounting.info.powerbi"
    _description = "Report - Info Contabilidad Power BI"
    _auto = False
    
    # Compañia
    fecha = fields.Date(string='Fecha', readonly=True)
    ano = fields.Integer(string='Año', readonly=True)
    mes = fields.Integer(string='Mes', readonly=True)
    id_account = fields.Integer(string='Id cuenta financiera', readonly=True)
    descripcion = fields.Char(string='Descripción', readonly=True)
    lineaAnalitica = fields.Char(string='Línea Analítica', readonly=True)
    familiaAnalitica = fields.Char(string='Familia Analítica', readonly=True)
    cuenta_analitica = fields.Char(string='Cuenta Analítica', readonly=True)
    ref = fields.Char(string='REF', readonly=True)
    tipo_Cuenta = fields.Char(string='Tipo Cuenta', readonly=True)
    grupo_Presupuestal = fields.Char(string='Grupo Presupuestal', readonly=True)
    grupo_Definitivo = fields.Char(string='Grupo Definitivo', readonly=True)
    cuenta_financiera = fields.Char(string='Cuenta Financiera', readonly=True)
    producto = fields.Char(string='Producto', readonly=True)
    cantidad = fields.Integer(string='Cantidad', readonly=True)
    unidad = fields.Char(string='Unidad', readonly=True)
    asociado = fields.Char(string='Asociado', readonly=True)
    compañia = fields.Char(string='Compañia', readonly=True)
    importe = fields.Integer(string='Importe', readonly=True)
    credit = fields.Integer(string='Haber', readonly=True)
    debit = fields.Integer(string='Debe', readonly=True)
    categoria = fields.Char(string='Etiqueta Analítica', readonly=True)
    creado = fields.Date(string='Creado', readonly=True)
    creado_por = fields.Char(string='Creado Por', readonly=True)
    modificado = fields.Date(string='Actualizado', readonly=True)
    actualizado_Por = fields.Char(string='Actualizado Por', readonly=True)
    
    @api.model
    def _select(self):
        #coalesce(e."x_studio_clase",'-') as clase,
        return '''
         select Row_Number() over (order by j."name") as ID,
             coalesce(a."date",'1900-01-01') as fecha,
            date_part('year',a."date") as ano,
            date_part('month',a."date")as mes,
            coalesce(e.id,0) as id_account, 
            coalesce(A."name",'-') as descripcion, 
            coalesce(q."name",'-') as lineaAnalitica,
            coalesce(p."name",'-') as familiaAnalitica,
            coalesce(d.code,'-') ||' / '|| coalesce(d.name,'-')  as cuenta_analitica,
            coalesce(a."ref",'-') as ref,
            coalesce(left(e.code,2),'0')  as tipo_Cuenta,
            coalesce(m."name",'-') as grupo_Presupuestal,
            --Mira, si es 5, 6 o 42 y el grupo pptal es NO APLICA o esta NULO, dejar la línea analitica, de lo contrario deje el grupo pptal.
            coalesce( case when (left(e.code,1) = '5' or left(e.code,1) = '6' or left(e.code,2) = '42')  and  m."name" = '000 NO APLICA' or m."name" is null  then coalesce(q."name",'-') else coalesce(m."name",'-') end ,'-') as grupo_Definitivo,
            coalesce(e.code,'-') ||' / '|| coalesce(e.name,'-') as cuenta_financiera,
            coalesce(b."name",'-') as apunte_contable, coalesce(b.product_id  ||' '||  coalesce(replace(g.name,'(copia)',''),'-') ||' '|| coalesce(pav.name,''),'-')  as  producto , 
            coalesce(b.quantity,'0') as cantidad,
            coalesce(h.name,'-') as unidad, 
            coalesce(i.display_name,'-') as asociado,
            coalesce(j."name",'-') as compañia, 
            coalesce(c.amount,b.balance*-1) as importe, 
            b.credit,  
            b.debit,
            coalesce(l."name",'-')  as categoria,
            coalesce(b."create_date",'1900-01-01') as creado, 
            coalesce(usu_crea.name,'-') as creado_por, 
            coalesce(b.write_date,'1900-01-01') as modificado,
            coalesce(usu_mod.name,'-') as Actualizado_Por
            From account_move a
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
            where (e.code like '4%' or e.code like '5%' or e.code like '6%') and a.state = 'posted' 
        ''' 

    def init(self):        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s 
            )
        ''' % (
            self._table, self._select()
        ))

    