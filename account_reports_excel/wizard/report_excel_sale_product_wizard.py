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
                raise Warning(_('!No hay resultados para los datos seleccionados¡'))
            self.make_file(value)

        path = "/web/binary/download_document?"
        model = "report.excel.sale.product.wizard"
        filename = self.data_name

        url = path + "model={}&id={}&filename={}.xlsx".format(
            model, self.id, filename)

        return {
            'type' : 'ir.actions.act_url',
            'url': url,
            'target': 'self',
            'tag': 'reload',
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
                                    pt.name,
                                    c.name as company,
                                    cta.name,
                                    ctal.name,
                                    gf.complete_name,
                                    gl.complete_name,
                                    mc.name,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    WHEN m.type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    t.name as equipodeventa,                                    
                                    m.x_send_dian,
                                    m.x_date_send_dian,
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
                                    LEFT JOIN account_analytic_account ctal on ctal.id=l.analytic_account_id     
                                    LEFT join account_analytic_group gf on gf.id=l.x_account_analytic_group
                                    LEFT join account_analytic_group gl on gl.id=l.x_account_analytic_group_two                                                                
                                    INNER JOIN res_currency mc on mc.id=m.currency_id
                                    where m.date between %s and %s
                                    and m.type in ('out_invoice', 'out_refund') and m.state='posted' 
                                    and exclude_from_invoice_tab is False and l.product_id=%s''', 
                                    (date_from, date_to, self.product_id.id))
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
                                    pt.name,
                                    c.name as company,
                                    cta.name,
                                    ctal.name,
                                    gf.complete_name,
                                    gl.complete_name,
                                    mc.name,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    WHEN m.type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    t.name as equipodeventa,                                    
                                    m.x_send_dian,
                                    m.x_date_send_dian,
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
                                    LEFT JOIN account_analytic_account ctal on ctal.id=l.analytic_account_id      
                                    LEFT join account_analytic_group gf on gf.id=l.x_account_analytic_group
                                    LEFT join account_analytic_group gl on gl.id=l.x_account_analytic_group_two
                                    INNER JOIN res_currency mc on mc.id=m.currency_id
                                    where m.date between %s and %s
                                    and m.type in ('out_invoice', 'out_refund') and m.state='posted' and exclude_from_invoice_tab is False ''', 
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
                                    pt.name,
                                    c.name as company,
                                    cta.name,
                                    ctal.name,
                                    gf.complete_name,
                                    gl.complete_name,
                                    mc.name,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    WHEN m.type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    t.name as equipodeventa,                                    
                                    m.x_send_dian,
                                    m.x_date_send_dian,
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
                                    LEFT JOIN account_analytic_account ctal on ctal.id=l.analytic_account_id     
                                    LEFT join account_analytic_group gf on gf.id=l.x_account_analytic_group
                                    LEFT join account_analytic_group gl on gl.id=l.x_account_analytic_group_two                                                                  
                                    where m.date between %s and %s
                                    and m.type in ('out_invoice', 'out_refund') and m.state='posted' 
                                    and exclude_from_invoice_tab is False AND m.company_id=%s and l.product_id=%s''', 
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
                                    pt.name,
                                    c.name as company,
                                    cta.name,
                                    ctal.name,
                                    gf.complete_name,
                                    gl.complete_name,
                                    mc.name,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_unit*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
                                    THEN l.debit*-1
                                    WHEN l.amount_currency<>0.0
                                    THEN l.credit
                                    ELSE l.price_unit
                                    END AS price_unit_by_product,
                                    l.quantity,   
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN ((l.price_unit*l.quantity)*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (((l.price_unit*l.quantity)-(round(((l.price_unit*l.discount)/100),2)))*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    WHEN m.type = 'out_refund' AND (select count(*) from account_move_line_account_tax_rel where account_move_line_id=l.id)>0
                                    THEN round((coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0)*-1),2)
                                    ELSE round(coalesce((((l.price_unit*l.quantity)-((l.price_unit*l.discount)/100))*0.19),0),2)
                                    END AS tax,
                                    CASE WHEN m.type = 'out_refund' and l.amount_currency=0.0
                                    THEN (l.price_total*-1)
                                    WHEN m.type = 'out_refund' and l.amount_currency<>0.0
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
                                    t.name as equipodeventa,                                    
                                    m.x_send_dian,
                                    m.x_date_send_dian,
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
                                    LEFT JOIN account_analytic_account ctal on ctal.id=l.analytic_account_id                                
                                    LEFT join account_analytic_group gf on gf.id=l.x_account_analytic_group
                                    LEFT join account_analytic_group gl on gl.id=l.x_account_analytic_group_two                                       
                                    where m.date between %s and %s
                                    and m.type in ('out_invoice', 'out_refund') and m.state='posted' 
                                    and exclude_from_invoice_tab is False AND m.company_id=%s''', 
                                    (date_from, date_to, company_id.id))

        lineas = self._cr.fetchall()
        return lineas


    def make_file(self, value):
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
        ws.write(0, 0, 'FACTURACIÓN POR PRODUCTO', title_head)
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
        ws.write(fila_title, 1, 'Cliente', subtitle_head)
        ws.write(fila_title, 2, 'NIT', subtitle_head)
        ws.write(fila_title, 3, 'Fecha de la factura', subtitle_head)
        ws.write(fila_title, 4, 'Fecha de Vencimiento', subtitle_head)
        ws.write(fila_title, 5, 'Documento Origen', subtitle_head)
        ws.write(fila_title, 6, 'Producto', subtitle_head)
        ws.write(fila_title, 7, 'Company', subtitle_head)
        ws.write(fila_title, 8, 'Red de Valor', subtitle_head)        
        ws.write(fila_title, 9, 'Cuenta Analitica', subtitle_head)   
        ws.write(fila_title, 10, 'Grupo Analitico Linea', subtitle_head)
        ws.write(fila_title, 11, 'Grupo Analitica Familia', subtitle_head)
        ws.write(fila_title, 12, 'Estado', subtitle_head)
        ws.write(fila_title, 13, 'Vendedor', subtitle_head)
        ws.write(fila_title, 14, 'Equipo de Venta', subtitle_head)
        ws.write(fila_title, 15, 'Enviado a la DIAN', subtitle_head)
        ws.write(fila_title, 16, 'Fecha de Envio a la DIAN', subtitle_head)        
        ws.write(fila_title, 17, 'CUFE', subtitle_head)
        ws.write(fila_title, 18, 'Moneda', subtitle_head)
        ws.write(fila_title, 19, 'Precio Unitario', subtitle_head)
        ws.write(fila_title, 20, 'Cantidad', subtitle_head)        
        ws.write(fila_title, 21, 'SubTotal', subtitle_head)        
        ws.write(fila_title, 22, 'Descuento', subtitle_head)
        ws.write(fila_title, 23, '% Descuento', subtitle_head)
        ws.write(fila_title, 24, 'Neto', subtitle_head)
        ws.write(fila_title, 25, 'Impuesto', subtitle_head)        
        ws.write(fila_title, 26, 'Total', subtitle_head)
        ws.write(fila_title, 27, 'Mes Fact', subtitle_head)
        ws.write(fila_title, 28, 'Año Fact', subtitle_head)

        fila=10
        for x in value:
            ws.write_row(fila,0,x)
            fila+=1

        try:
            wb.close()
            out = base64.encodestring(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'FacturaXproducto' + '-' + str(date_file)
        except ValueError:
            raise Warning('No se pudo generar el archivo')

    def get_values_product_company(self, date_from, date_to, company_id):
        value = []
        self._cr.execute(''' select 
                                c.name as company,
                                pt.name,
                                CASE WHEN m.type = 'out_refund' and sum(l.amount_currency)=0.0
                                THEN (((sum(l.price_unit)*sum(l.quantity))-(round(((sum(l.price_unit)*sum(l.discount))/100),2)))*-1)
                                WHEN m.type = 'out_refund' and sum(l.amount_currency)<>0.0
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
                                and m.type in ('out_invoice', 'out_refund') and m.state='posted' 
                                and exclude_from_invoice_tab is False and c.id=%s GROUP BY c.name, pt.name, m.type ''', 
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
            out = base64.encodestring(buf.getvalue())
            buf.close()
            date_file = fields.Datetime.now()
            self.data = out
            self.data_name = 'FacturaXproducto' + '-' + str(date_file)
        except ValueError:
            raise Warning('No se pudo generar el archivo')