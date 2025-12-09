# -*- coding: utf-8 -*-

from odoo import tools, api, fields, models
import logging

_logger = logging.getLogger(__name__)


class InvoiceAnalyticsReport(models.Model):
    _name = "invoice.analytics.report"
    _auto = False
    _description = "Reporte Analítico de Facturas"
    _order = "invoice_date desc, partner_vat"

    # Campos básicos
    id = fields.Integer('ID', readonly=True)
    partner_vat = fields.Char('NIT', readonly=True)
    partner_name = fields.Char('Cliente', readonly=True)
    invoice_name = fields.Char('Factura', readonly=True)
    invoice_date = fields.Date('Fecha Factura', readonly=True)
    invoice_date_due = fields.Date('Fecha Vencimiento', readonly=True)
    invoice_month = fields.Integer('Mes Facturación', readonly=True)
    invoice_year = fields.Integer('Año Facturación', readonly=True)
    
    # Información de pago
    payment_term = fields.Char('Plazo de Pago', readonly=True)
    payment_state = fields.Char('Estado de Pago', readonly=True)
    
    # Montos
    amount_untaxed = fields.Float('Subtotal', readonly=True)
    
    # Información de producto
    product_name = fields.Char('Producto Facturado', readonly=True)
    invoice_type = fields.Char('Tipo de Facturación', readonly=True)
    
    # Información de equipo y vendedor
    team_name = fields.Char('Equipo de Ventas', readonly=True)
    salesperson_name = fields.Char('Vendedor', readonly=True)
    
    # Información de vinculación
    vinculation_type = fields.Char('Tipo de Vinculación', readonly=True)
    vinculation_date = fields.Date('Fecha de Vinculación', readonly=True)
    
    # Clasificación del partner
    sector_name = fields.Char('Sector', readonly=True)
    company_size = fields.Char('Tamaño de Empresa', readonly=True)
    red_value = fields.Char('Red de Valor', readonly=True)
    member_type = fields.Char('Tipo de Miembro', readonly=True)


    def _select(self):
        select_str = """
        SELECT 
            ROW_NUMBER() OVER (ORDER BY m.date DESC, p.vat) as id,
            CASE WHEN p.id is not null
                THEN p.vat
                ELSE pta.vat
            END AS partner_vat,
            CASE WHEN p.parent_id is not null
                THEN pta.name
                ELSE p.name
            END AS partner_name,
            m.name as invoice_name,
            m.date as invoice_date,
            m.invoice_date_due as invoice_date_due,
            date_part('month', m.date) AS invoice_month,
            date_part('year', m.date) AS invoice_year,
            CASE
                WHEN tp.name->>'es_CO' IS NOT NULL THEN tp.name->>'es_CO'
                ELSE tp.name->>'en_US'
            END AS payment_term,
            m.amount_untaxed_signed as amount_untaxed,
            (
                SELECT 
                    CASE 
                        WHEN pt2.name->>'es_CO' IS NOT NULL THEN pt2.name->>'es_CO'
                        ELSE pt2.name->>'en_US'
                    END
                FROM account_move_line l2
                LEFT JOIN product_product pp2 ON pp2.id = l2.product_id
                LEFT JOIN product_template pt2 ON pt2.id = pp2.product_tmpl_id
                WHERE l2.move_id = m.id
                  AND l2.product_id IS NOT NULL
                ORDER BY l2.id
                LIMIT 1
            ) AS product_name,
            (
                SELECT 
                    CASE
                        WHEN pt2.id = 3 THEN 'Renovación Aportes'
                        WHEN pt2.id = 1605 THEN 'Nueva'
                        WHEN pt2.id = 9 THEN 'Reactivación'
                        ELSE NULL
                    END
                FROM account_move_line l2
                LEFT JOIN product_product pp2 ON pp2.id = l2.product_id
                LEFT JOIN product_template pt2 ON pt2.id = pp2.product_tmpl_id
                WHERE l2.move_id = m.id
                  AND l2.product_id IS NOT NULL
                ORDER BY l2.id
                LIMIT 1
            ) AS invoice_type,
            CASE
                WHEN cti.name->>'es_CO' IS NOT NULL THEN cti.name->>'es_CO'
                ELSE cti.name->>'en_US'
            END AS team_name,
            pucti.name as salesperson_name,
            CASE WHEN vinc.tipos_vinculacion is not null
                THEN vinc.tipos_vinculacion
                ELSE vincpa.tipos_vinculacion
            END AS vinculation_type,
            CASE WHEN p.x_date_vinculation is not null
                THEN p.x_date_vinculation
                ELSE pta.x_date_vinculation
            END AS vinculation_date,
            CASE 
                WHEN sie.name IS NOT NULL THEN sie.name
                ELSE siepta.name
            END AS sector_name,
            CASE 
                WHEN COALESCE(p.x_company_size, pta.x_company_size) IS NULL
                    THEN NULL
                WHEN COALESCE(p.x_company_size, pta.x_company_size) = '1'
                    THEN 'MYPE'
                WHEN COALESCE(p.x_company_size, pta.x_company_size) = '2'
                    THEN 'MYPE'
                WHEN COALESCE(p.x_company_size, pta.x_company_size) = '3'
                    THEN 'MEDIANA'
                WHEN COALESCE(p.x_company_size, pta.x_company_size) = '4'
                    THEN 'GRANDE'
                WHEN COALESCE(p.x_company_size, pta.x_company_size) = '5'
                    THEN 'MYPE'
                ELSE 'MYPE'
            END AS company_size,
            CASE 
                WHEN redv.name IS NOT NULL THEN redv.name
                ELSE redvsiepta.name
            END AS red_value,
            CASE 
                WHEN p.type_member IS NOT NULL THEN p.type_member
                ELSE pta.type_member
            END AS member_type,
            m.payment_state
        """
        return select_str

    def _from(self):
        from_str = """
        FROM account_move m 
        INNER JOIN account_move_line l ON l.move_id = m.id 
        INNER JOIN res_partner p ON p.id = m.partner_id 
        LEFT JOIN res_partner pta ON pta.id = p.parent_id
        LEFT JOIN product_product pp ON l.product_id = pp.id 
        LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
        LEFT JOIN product_variant_combination pvc ON pvc.product_product_id = pp.id
        LEFT JOIN product_template_attribute_value ptav ON ptav.id = pvc.product_template_attribute_value_id
        LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id
        LEFT JOIN product_attribute pa ON pa.id = pav.attribute_id
        LEFT JOIN (
            SELECT
                vp.res_partner_id,
                string_agg(DISTINCT v.name, ' | ' ORDER BY v.name) AS tipos_vinculacion
            FROM logyca_vinculation_types_res_partner_rel vp
            JOIN logyca_vinculation_types v
              ON v.id = vp.logyca_vinculation_types_id
            GROUP BY vp.res_partner_id
        ) vinc ON vinc.res_partner_id = p.id
        LEFT JOIN (
            SELECT
                vpta.res_partner_id,
                string_agg(DISTINCT vt.name, ' | ' ORDER BY vt.name) AS tipos_vinculacion
            FROM logyca_vinculation_types_res_partner_rel vpta
            JOIN logyca_vinculation_types vt
              ON vt.id = vpta.logyca_vinculation_types_id
            GROUP BY vpta.res_partner_id
        ) vincpa ON vincpa.res_partner_id = pta.id
        LEFT JOIN account_payment_term tp ON tp.id = m.invoice_payment_term_id
        INNER JOIN crm_team cti ON cti.id = m.team_id
        INNER JOIN res_users ucti ON ucti.id = m.invoice_user_id
        INNER JOIN res_partner pucti ON ucti.partner_id = pucti.id
        LEFT JOIN logyca_sectors sie ON sie.id = p.x_sector_id
        LEFT JOIN logyca_sectors siepta ON siepta.id = pta.x_sector_id
        LEFT JOIN logyca_member_red redv ON redv.id = p.member_red_id
        LEFT JOIN logyca_member_red redvsiepta ON redvsiepta.id = pta.member_red_id
        """
        return from_str

    def _where(self):
        where_str = """
        WHERE m.date > '2025-01-01' 
            AND m.state = 'posted'
            AND m.move_type IN ('out_invoice', 'out_refund')
            AND l.product_id IS NOT NULL
            AND pt.id IN (9, 1605, 3)
        """
        return where_str

    def init(self):
        """
        Crea o reemplaza la vista PostgreSQL con la query optimizada
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where())
        
        _logger.info("Creando vista: %s", self._table)
        # _logger.debug("SQL Query: %s", sql)  # Descomentar para debug
        self.env.cr.execute(sql)
