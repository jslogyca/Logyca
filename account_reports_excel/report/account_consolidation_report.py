# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
from datetime import date
import logging
_logger = logging.getLogger(__name__)


class AccountConsolidationReport(models.Model):
    _name = "account.consolidation.report"
    _auto = False
    _description = "Consolidación por Cuenta Contable"
    _order = "account_code"

    id = fields.Integer('ID', readonly=True)
    account_id = fields.Many2one('account.account', 'Cuenta Contable', readonly=True)
    account_code = fields.Char('Código Cuenta', readonly=True)
    account_name = fields.Char('Nombre Cuenta', readonly=True)
    company_id = fields.Many2one('res.company', 'Compañía', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Moneda Local', readonly=True)
    
    # Consolidación de valores
    total_amount_currency = fields.Float(
        string='Total Moneda Extranjera',
        digits='Account',
        readonly=True,
        help='Suma de valores en moneda diferente a la local (amount_currency)'
    )
    total_balance = fields.Float(
        string='Balance Total',
        digits='Account',
        readonly=True,
        help='Suma de todos los balances de los apuntes contables'
    )
    
    # Fecha de corte
    date_to = fields.Date(
        string='Fecha de Corte',
        readonly=True,
        default=fields.Date.context_today
    )
    
    # Campos adicionales útiles
    count_lines = fields.Integer(
        string='Cantidad de Apuntes',
        readonly=True,
        help='Número de apuntes contables de esta cuenta'
    )

    def _select(self):
        select_str = """
            SELECT 
                MIN(l.id) as id,
                l.account_id as account_id,
                a.code as account_code,
                CASE 
                    WHEN jsonb_typeof(a.name) = 'object' THEN 
                        COALESCE(
                            a.name::jsonb->>'es_CO',
                            a.name::jsonb->>'en_US',
                            a.name::text
                        )
                    ELSE 
                        a.name::text
                END as account_name,
                l.company_id as company_id,
                c.currency_id as currency_id,
                
                -- Suma de valores en moneda extranjera (donde la moneda es diferente a la local)
                SUM(CASE 
                    WHEN l.currency_id IS NOT NULL 
                         AND l.currency_id != c.currency_id 
                    THEN l.amount_currency 
                    ELSE 0 
                END) as total_amount_currency,
                
                -- Suma de todos los balances
                SUM(l.balance) as total_balance,
                
                -- Fecha de corte (usamos la fecha máxima como referencia)
                MAX(l.date) as date_to,
                
                -- Cantidad de líneas
                COUNT(l.id) as count_lines
        """
        return select_str

    def _from(self):
        from_str = """
            account_move_line l
            INNER JOIN account_account a ON l.account_id = a.id
            INNER JOIN res_company c ON l.company_id = c.id
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE l.parent_state = 'posted'
              AND l.date <= CURRENT_DATE
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY 
                l.account_id,
                a.code,
                a.name,
                l.company_id,
                c.currency_id
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """
            CREATE OR REPLACE VIEW %s AS (
                %s
                FROM %s
                %s
                %s
            )
        """ % (
            self._table,
            self._select(),
            self._from(),
            self._where(),
            self._group_by()
        )
        
        _logger.info('Creating view: %s', self._table)
        print('SQL:', sql)
        self.env.cr.execute(sql)

    @api.model
    def get_consolidation_by_date(self, date_to=None):
        """
        Método para obtener la consolidación filtrada por fecha
        
        :param date_to: Fecha de corte (si no se proporciona, usa la fecha actual)
        :return: Recordset con los datos consolidados
        """
        if not date_to:
            date_to = fields.Date.context_today(self)
        
        # Consulta SQL dinámica con fecha de corte
        query = """
            SELECT 
                MIN(l.id) as id,
                l.account_id,
                a.code as account_code,
                CASE 
                    WHEN jsonb_typeof(a.name) = 'object' THEN 
                        COALESCE(
                            a.name::jsonb->>'es_CO',
                            a.name::jsonb->>'en_US',
                            a.name::text
                        )
                    ELSE 
                        a.name::text
                END as account_name,
                l.company_id,
                c.currency_id,
                SUM(CASE 
                    WHEN l.currency_id IS NOT NULL 
                         AND l.currency_id != c.currency_id 
                    THEN l.amount_currency 
                    ELSE 0 
                END) as total_amount_currency,
                SUM(l.balance) as total_balance,
                %s::date as date_to,
                COUNT(l.id) as count_lines
            FROM account_move_line l
            INNER JOIN account_account a ON l.account_id = a.id
            INNER JOIN res_company c ON l.company_id = c.id
            WHERE l.parent_state = 'posted'
              AND l.date <= %s
            GROUP BY 
                l.account_id,
                a.code,
                a.name,
                l.company_id,
                c.currency_id
            ORDER BY a.code
        """
        
        self.env.cr.execute(query, (date_to, date_to))
        results = self.env.cr.dictfetchall()
        
        return results
