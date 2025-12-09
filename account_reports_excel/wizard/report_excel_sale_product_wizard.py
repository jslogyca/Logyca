# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import xlwt
import base64
import io
import xlsxwriter
import requests

class ReportExcelSaleProductWizard(models.TransientModel):
    _name = 'report.excel.sale.product.wizard'
    _description = 'Report Excel Sale Product Wizard'

    date_from = fields.Date(string='Fecha de Inicio')
    date_to = fields.Date(string='Fecha Fin')
    data = fields.Binary("Archivo")
    data_name = fields.Char("nombre del archivo")    
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    all_company = fields.Boolean(string='Todas las Compañías', default=True)
    product_id = fields.Many2one('product.product', string='Producto')
    by_product_company = fields.Boolean(string='By Product and Company', default=False)

    def do_report(self):
        if self.by_product_company:
            self.make_file_product_company()
        else:
            if self.all_company:
                value = self.get_values(self.date_from, self.date_to)
            else:
                value = self.get_values_by_company(self.date_from, self.date_to, self.company_id)

            if not value:
                raise ValidationError(_('¡No hay resultados para los datos seleccionados!'))

            self.make_file(value)

        if not self.data:
            raise ValidationError("No se generó el archivo correctamente.")

        return {
            'type': 'ir.actions.act_url',
            'url': f"/web/content?model=report.excel.sale.product.wizard&id={self.id}&field=data&filename_field=data_name&download=true",
            'target': 'self',
        }

          


    def get_values(self, date_from, date_to):
        value = []
        if self.product_id:
            self._cr.execute(''' select 
                                    p.vat,
                                    CASE WHEN p.parent_id IS NULL 
                                    THEN p.name 
                                    ELSE pp.name
                                    END AS asociado,                                    
                                    m.name as factura,
                                    to_char(m.invoice_date,'YYYY/MM/DD'),
                                    to_char(m.invoice_date_due,'YYYY/MM/DD'),
                                    date_part('month',m.invoice_date)as mes_fact,
                                    date_part('year',m.invoice_date)as year_fact,
                                    m.invoice_origin,
                                    CASE WHEN pt.name->>'es_CO' is not null
                                    THEN pt.name->>'es_CO'
                                    ELSE pt.name->>'en_US'
                                    END as nombre_producto,
                                    c.name as company,
                                    cta.name,
                                    aaa.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' as plan,
                                    mc.name,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE (l.price_unit*l.quantity)
                                    END AS price_unit,
                                    CASE WHEN l.discount>0
                                    THEN round(((l.price_unit*l.discount)/100),2)
                                    ELSE 0.0
                                    END AS discount,
                                    l.discount,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
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
                                    WHEN m.move_type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_total
                                    END AS price_total,
                                    CASE WHEN m.state='posted'
                                    THEN 'Publicada'
                                    ELSE 'Borrador'
                                    END AS estado,                                    
                                    pu.name as vendedor,
                                    t.name->>'es_CO' AS equipodeventa,
                                    m.x_send_dian,
                                    to_char(m.x_date_send_dian,'YYYY/MM/DD'),
                                    m.x_cufe_dian                               
                                    from account_move m
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
                                    INNER JOIN res_currency mc on mc.id=m.currency_id
                                    JOIN LATERAL jsonb_each(l.analytic_distribution) AS dist(key, value) ON TRUE
                                    LEFT JOIN account_analytic_account aaa ON aaa.id::text = key
                                    INNER JOIN account_analytic_plan pla on pla.id=aaa.plan_id                                    
                                    where m.date between %s and %s
                                    and m.move_type in ('out_invoice', 'out_refund') and m.state='posted' and l.product_id=%s''', 
                                    (date_from, date_to, self.product_id.id))
        else:
            self._cr.execute(''' SELECT 
                                    p.vat,
                                    CASE 
                                    WHEN p.parent_id IS NULL THEN p.name 
                                    ELSE pp.name
                                    END AS asociado,                                    
                                    m.name AS factura,
                                    to_char(m.invoice_date,'YYYY/MM/DD') AS fecha_factura,
                                    to_char(m.invoice_date_due,'YYYY/MM/DD') AS fecha_vencimiento,
                                    date_part('month', m.invoice_date) AS mes_fact,
                                    date_part('year', m.invoice_date) AS year_fact,
                                    m.invoice_origin,
                                    CASE 
                                    WHEN pt.name->>'es_CO' IS NOT NULL THEN pt.name->>'es_CO'
                                    ELSE pt.name->>'en_US'
                                    END AS nombre_producto,
                                    c.name AS company,
                                    cta.name AS cuenta_analitica_mov,
                                    aaa.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' AS plan,
                                    mc.name AS moneda,

                                    -- Precio unitario por producto con manejo de NC y multi-moneda
                                    CASE 
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN ((l.price_unit * -1)/l.quantity)
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN (l.debit * -1)/l.quantity
                                    WHEN l.amount_currency <> 0.0 THEN (l.credit/l.quantity)
                                    ELSE (l.price_unit/l.quantity)
                                    END AS price_unit_by_product,

                                    l.quantity,

                                    -- Neto: (total - subtotal) - descuento
                                    CASE 
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN ((l.price_unit * -1) * l.quantity) / l.quantity
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN ((l.debit * -1) * l.quantity) / l.quantity
                                    WHEN l.amount_currency <> 0.0 THEN (l.credit * l.quantity) / l.quantity
                                    ELSE (l.price_unit * l.quantity) / l.quantity
                                    END AS base_sin_impuesto,



                                    -- Valor de descuento en dinero
                                    CASE 
                                    WHEN l.discount > 0 THEN 
                                    ROUND((l.price_unit * l.quantity) * (l.discount / 100.0), 2)
                                    ELSE 0.0
                                    END AS discount,

                                    -- Porcentaje de descuento
                                    l.discount AS discount_percent,

                                    -- Neto: (total - subtotal) - descuento
                                    -- CASE 
                                    -- WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN ((l.price_unit * -1) * l.quantity) - ROUND((l.price_unit * l.quantity) * (l.discount / 100.0), 2)
                                    -- WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN ((l.debit * -1) * l.quantity) - ROUND((l.debit * l.quantity) * (l.discount / 100.0), 2)
                                    -- WHEN l.amount_currency <> 0.0 THEN (l.credit * l.quantity) - ROUND((l.credit * l.quantity) * (l.discount / 100.0), 2)
                                    -- ELSE (l.price_unit * l.quantity) - ROUND((l.price_unit * l.quantity) * (l.discount / 100.0), 2)
                                    -- END AS neto,

                                    CASE 
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN ((l.price_unit * -1) * l.quantity) / l.quantity 
                                    WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN ((l.debit * -1) * l.quantity) / l.quantity
                                    WHEN l.amount_currency <> 0.0 THEN (l.credit * l.quantity) / l.quantity
                                    ELSE (l.price_unit * l.quantity) / l.quantity
                                    END AS neto,

                                    -- Impuesto de la línea = total - subtotal
                                    -- (l.price_total - l.price_subtotal) AS tax,    
                                    -- (m.amount_tax_signed) AS tax,

                                    CASE 
                                        WHEN m.amount_tax_signed <> 0 AND pt.id not in (1605, 1606) THEN 
                                            ROUND(
                                                CASE 
                                                    WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN (l.price_unit * -1) * l.quantity
                                                    WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN (l.debit * -1)
                                                    WHEN l.amount_currency <> 0.0 THEN (l.credit)
                                                    ELSE (l.price_unit * l.quantity)
                                                END * 0.19
                                            , 2)
                                        ELSE 0
                                    END AS tax,

                                    -- Total de la línea
                                    -- l.price_total AS price_total,
                                    -- m.amount_total_signed AS price_total,
                                    CASE 
                                        WHEN m.amount_tax_signed <> 0 AND pt.id not in (1605, 1606) THEN
                                            ROUND(
                                                CASE 
                                                    WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN (l.price_unit * -1) * l.quantity
                                                    WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN (l.debit * -1)
                                                    WHEN l.amount_currency <> 0.0 THEN (l.credit)
                                                    ELSE (l.price_unit * l.quantity)
                                                END * 1.19
                                            , 2)
                                        ELSE 
                                            -- Si no hay impuesto, el total es igual al neto
                                            CASE 
                                                WHEN m.move_type = 'out_refund' AND l.amount_currency = 0.0 THEN (l.price_unit * -1) * l.quantity
                                                WHEN m.move_type = 'out_refund' AND l.amount_currency <> 0.0 THEN (l.debit * -1) * l.quantity
                                                WHEN l.amount_currency <> 0.0 THEN (l.credit * l.quantity)
                                                ELSE (l.price_unit * l.quantity)
                                            END
                                    END AS price_total,                                   

                                    CASE 
                                    WHEN m.state = 'posted' THEN 'Publicada'
                                    ELSE 'Borrador'
                                    END AS estado,                                    

                                    pu.name AS vendedor,
                                    t.name->>'es_CO' AS equipodeventa,
                                    m.x_send_dian,
                                    to_char(m.x_date_send_dian,'YYYY/MM/DD') AS fecha_envio_dian,
                                    m.x_cufe_dian                              

                                    FROM account_move m
                                    INNER JOIN account_move_line l 
                                    ON m.id = l.move_id
                                    INNER JOIN res_partner p 
                                    ON p.id = m.partner_id
                                    INNER JOIN product_product ppt 
                                    ON ppt.id = l.product_id
                                    INNER JOIN product_template pt 
                                    ON pt.id = ppt.product_tmpl_id
                                    LEFT JOIN res_partner pp 
                                    ON p.parent_id = pp.id
                                    INNER JOIN res_company c 
                                    ON c.id = m.company_id
                                    INNER JOIN res_users u 
                                    ON u.id = m.invoice_user_id
                                    INNER JOIN res_partner pu 
                                    ON pu.id = u.partner_id
                                    INNER JOIN crm_team t 
                                    ON t.id = m.team_id
                                    LEFT JOIN account_analytic_account cta 
                                    ON cta.id = m.analytic_account_id
                                    INNER JOIN res_currency mc 
                                    ON mc.id = m.currency_id
                                    JOIN LATERAL jsonb_each(l.analytic_distribution) AS dist(key, value) 
                                    ON TRUE
                                    LEFT JOIN account_analytic_account aaa 
                                    ON aaa.id::text = key
                                    INNER JOIN account_analytic_plan pla 
                                    ON pla.id = aaa.plan_id                                    

                                    WHERE m.date BETWEEN %s AND %s
                                    AND m.move_type IN ('out_invoice', 'out_refund') 
                                    AND m.state = 'posted'

                                     ''', 
                                    (date_from, date_to))
        
        lineas = self._cr.fetchall()
        return lineas


    def get_values_by_company(self, date_from, date_to, company_id):
        value = []
        if self.product_id:
            self._cr.execute(''' select 
                                    p.vat,
                                    CASE WHEN p.parent_id IS NULL 
                                    THEN p.name 
                                    ELSE pp.name
                                    END AS asociado,                                    
                                    m.name as factura,
                                    to_char(m.invoice_date,'YYYY/MM/DD'),
                                    to_char(m.invoice_date_due,'YYYY/MM/DD'),
                                    date_part('month',m.invoice_date)as mes_fact,
                                    date_part('year',m.invoice_date)as year_fact,
                                    m.invoice_origin,
                                    CASE WHEN pt.name->>'es_CO' is not null
                                    THEN pt.name->>'es_CO'
                                    ELSE pt.name->>'en_US'
                                    END as nombre_producto,
                                    c.name as company,
                                    cta.name,
                                    aaa.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' as plan,
                                    mc.name,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE (l.price_unit*l.quantity)
                                    END AS price_unit,
                                    CASE WHEN l.discount>0
                                    THEN round(((l.price_unit*l.discount)/100),2)
                                    ELSE 0.0
                                    END AS discount,
                                    l.discount,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
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
                                    WHEN m.move_type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_total
                                    END AS price_total,
                                    CASE WHEN m.state='posted'
                                    THEN 'Publicada'
                                    ELSE 'Borrador'
                                    END AS estado,                                    
                                    pu.name as vendedor,
                                    t.name->>'es_CO' AS equipodeventa,
                                    m.x_send_dian,
                                    to_char(m.x_date_send_dian,'YYYY/MM/DD'),
                                    m.x_cufe_dian                               
                                    from account_move m
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
                                    INNER JOIN res_currency mc on mc.id=m.currency_id
                                    JOIN LATERAL jsonb_each(l.analytic_distribution) AS dist(key, value) ON TRUE
                                    LEFT JOIN account_analytic_account aaa ON aaa.id::text = key
                                    INNER JOIN account_analytic_plan pla on pla.id=aaa.plan_id                                    
                                    where m.date between %s and %s
                                    and m.move_type in ('out_invoice', 'out_refund') and m.state='posted' AND m.company_id=%s and l.product_id=%s''', 
                                    (date_from, date_to, company_id.id, self.product_id.id))
        else:
            self._cr.execute(''' select 
                                    p.vat,
                                    CASE WHEN p.parent_id IS NULL 
                                    THEN p.name 
                                    ELSE pp.name
                                    END AS asociado,                                    
                                    m.name as factura,
                                    to_char(m.invoice_date,'YYYY/MM/DD'),
                                    to_char(m.invoice_date_due,'YYYY/MM/DD'),
                                    date_part('month',m.invoice_date)as mes_fact,
                                    date_part('year',m.invoice_date)as year_fact,
                                    m.invoice_origin,
                                    CASE WHEN pt.name->>'es_CO' is not null
                                    THEN pt.name->>'es_CO'
                                    ELSE pt.name->>'en_US'
                                    END as nombre_producto,
                                    c.name as company,
                                    cta.name,
                                    aaa.name->>'es_CO' AS analytic_account_name,
                                    pla.name->>'es_CO' as plan,
                                    mc.name,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE (l.price_unit*l.quantity)
                                    END AS price_unit,
                                    CASE WHEN l.discount>0
                                    THEN round(((l.price_unit*l.discount)/100),2)
                                    ELSE 0.0
                                    END AS discount,
                                    l.discount,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
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
                                    WHEN m.move_type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.move_type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.move_type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_total
                                    END AS price_total,
                                    CASE WHEN m.state='posted'
                                    THEN 'Publicada'
                                    ELSE 'Borrador'
                                    END AS estado,                                    
                                    pu.name as vendedor,
                                    t.name->>'es_CO' AS equipodeventa,
                                    m.x_send_dian,
                                    to_char(m.x_date_send_dian,'YYYY/MM/DD'),
                                    m.x_cufe_dian                               
                                    from account_move m
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
                                    INNER JOIN res_currency mc on mc.id=m.currency_id
                                    JOIN LATERAL jsonb_each(l.analytic_distribution) AS dist(key, value) ON TRUE
                                    LEFT JOIN account_analytic_account aaa ON aaa.id::text = key
                                    INNER JOIN account_analytic_plan pla on pla.id=aaa.plan_id                                    
                                    where m.date between %s and %s
                                    and m.move_type in ('out_invoice', 'out_refund') and m.state='posted' AND m.company_id=%s''', 
                                    (date_from, date_to, company_id.id))

        lineas = self._cr.fetchall()
        return lineas


    def make_file(self, value):
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        date_file = fields.Datetime.now()

        # Formatos
        title_head = wb.add_format({
            'bold': 1,
            'border': 0,
            'align': 'right',
            'valign': 'vcenter'
        })
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)

        subtitle_head = wb.add_format({
            'bold': 1,
            'border': 1,
            'align': 'right',
            'fg_color': 'orange',
            'valign': 'vcenter'
        })
        subtitle_head.set_font_name('Arial')
        subtitle_head.set_font_size(10)

        user = self.env.user
        ws.write(0, 0, 'FACTURACIÓN POR PRODUCTO', title_head)
        ws.write(1, 0, str(user.company_id.name), title_head)
        ws.write(3, 0, 'Fecha Inicio', title_head)
        ws.write(3, 1, str(self.date_from))
        ws.write(4, 0, 'Fecha Fin', title_head)
        ws.write(4, 1, str(self.date_to))
        ws.write(5, 0, 'Usuario', title_head)
        ws.write(5, 1, str(user.partner_id.name))
        ws.write(6, 0, 'Fecha Archivo', title_head)
        ws.write(6, 1, str(date_file))

        fila_title = 9
        headers = [
            'NIT', 'Cliente', 'Factura', 'Fecha de la factura', 'Fecha de Vencimiento',
            'Mes Fact', 'Año Fact', 'Documento Origen', 'Producto', 'Company',
            'Red de Valor', 'Cuenta Analitica', 'Grupo Analitico Linea',
            'Moneda', 'Precio Unitario', 'Cantidad',
            'SubTotal', 'Descuento', '% Descuento', 'Neto', 'Impuesto', 'Total',
            'Estado', 'Vendedor', 'Equipo de Venta', 'Enviado a la DIAN',
            'Fecha de Envio a la DIAN', 'CUFE'
        ]
        for col, header in enumerate(headers):
            ws.write(fila_title, col, header, subtitle_head)

        fila = fila_title + 1
        for x in value:
            # Limpieza de diccionarios: extrae traducción si aplica
            clean_row = tuple(
                v.get(self.env.lang, str(v)) if isinstance(v, dict) else v
                for v in x
            )
            ws.write_row(fila, 0, clean_row)
            fila += 1

        try:
            wb.close()
            out = base64.b64encode(buf.getvalue())
            buf.close()
            safe_date = date_file.strftime('%Y-%m-%d_%H-%M-%S')
            self.data_name = f'FacturaXproducto-{safe_date}.xlsx'
            self.data = out
        except Exception as e:
            raise ValidationError(f'No se pudo generar el archivo: {e}')

    def get_values_product_company(self, date_from, date_to, company_id):
        value = []
        self._cr.execute(''' select 
                                c.name as company,
                                pt.name,
                                CASE WHEN m.move_type = 'out_refund' and sum(l.amount_currency)=0.0
                                THEN (((sum(l.price_unit)*sum(l.quantity))-(round(((sum(l.price_unit)*sum(l.discount))/100),2)))*-1)
                                WHEN m.move_type = 'out_refund' and sum(l.amount_currency)<>0.0
                                THEN sum(l.debit)*-1
                                WHEN sum(l.amount_currency)<>0.0
                                THEN sum(l.credit)
                                ELSE ((sum(l.price_unit)*sum(l.quantity))-(round(((sum(l.price_unit)*sum(l.discount))/100),2)))
                                END AS neto
                                from account_move m
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
                                where m.date between %s and %s
                                and m.move_type in ('out_invoice', 'out_refund') and m.state='posted' 
                                and exclude_from_invoice_tab is False and c.id=%s GROUP BY c.name, pt.name, m.move_type ''', 
                                (date_from, date_to, company_id.id))
        
        lineas = self._cr.fetchall()
        return lineas

    def make_file_product_company(self):
        buf = io.BytesIO()
        wb = xlsxwriter.Workbook(buf)
        ws = wb.add_worksheet('Report')
        date_file = fields.Datetime.now()
        
        #formatos
        title_head = wb.add_format({
                        'bold': 1,
                        'border': 0,
                        'align': 'rigth',
                        'valign': 'vcenter'})
        title_head.set_font_name('Arial')
        title_head.set_font_size(10) 
        
        subtitle_head = wb.add_format({
                        'bold': 1,
                        'border': 1,
                        'align': 'rigth',
                        'fg_color': 'orange',
                        'valign': 'vcenter'})
        title_head.set_font_name('Arial')
        title_head.set_font_size(10)
        
        user = self.env['res.users'].browse(self._uid)
        ws.write(0, 0, 'FACTURACIÓN POR PRODUCTO Y COMPAÑÍA', title_head)
        ws.write(1, 0, str(user.company_id.name), title_head)
        ws.write(3, 0, 'Fecha Inicio', title_head)
        ws.write(3, 1, str(self.date_from))
        ws.write(4, 0, 'Fecha Inicio', title_head)
        ws.write(4, 1, str(self.date_to))
        ws.write(5, 0, 'Usuario', title_head)
        ws.write(5, 1, str(user.partner_id.name))
        ws.write(6, 0, 'Fecha Archivo', title_head)
        ws.write(6, 1, str(date_file))

        fila_title=9
        ws.write(fila_title, 0, 'Factura', subtitle_head)
        ws.write(fila_title, 1, 'Producto', subtitle_head)
        ws.write(fila_title, 2, 'Neto', subtitle_head)

        fila=10
        if self.all_company:
            company_ids = self.env['res.company'].search([])
        else:
            company_ids = self.env['res.company'].search([('id', '=', self.company_id.id)])
        for company_id in company_ids:
            value = self.get_values_product_company(self.date_from, self.date_to, company_id)
            for x in value:
                ws.write_row(fila,0,x)
                fila+=1

        try:
            wb.close()
            out = base64.b64encode(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'FacturaXproducto' + '-' + str(date_file)
        except ValueError:
            raise Warning('No se pudo generar el archivo')