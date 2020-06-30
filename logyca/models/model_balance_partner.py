# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api

from functools import lru_cache


class AccountBalancePartnerFilter(models.TransientModel):
    _name = "account.balance.partner.filter"
    _description = "Filter - Balance Partner"
    
    date_filter = fields.Date(string='Fecha', required=True)
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "Fecha: {}".format(record.date_filter)))
        return result
    
    def open_pivot_view(self):
        ctx = self.env.context.copy()
        ctx.update({'date_filter':self.date_filter})
        self.env['account.balance.partner.report'].with_context(ctx).init()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pivot Balance',
            'res_model': 'account.balance.partner.report',
            'domain': [],
            'view_mode': 'pivot',
            'context': ctx
        }
    
class AccountBalancePartnerReport(models.Model):
    _name = "account.balance.partner.report"
    _description = "Report - Balance Partner"
    _auto = False
    _rec_name = 'account_level_one'
    _order = 'account_level_one,account_level_two,account_level_three,account_level_four,account_level_five'

    # Compañia
    company_id = fields.Many2one('res.company', string='Compañia', readonly=True)
    # Cuenta y sus niveles
    account_level_one = fields.Char(string='Cuenta Nivel 1', readonly=True)
    account_level_two = fields.Char(string='Cuenta Nivel 2', readonly=True)
    account_level_three = fields.Char(string='Cuenta Nivel 3', readonly=True) 
    account_level_four = fields.Char(string='Cuenta Nivel 4', readonly=True)
    account_level_five = fields.Char(string='Cuenta Nivel 5', readonly=True)
    # Cliente
    partner = fields.Char(string='Cliente', readonly=True)
    # Valores
    initial_balance = fields.Float(string='Saldo Anterior', default=0.0)
    debit = fields.Float(string='Débito', default=0.0)
    credit = fields.Float(string='Crédito', default=0.0)
    new_balance = fields.Float(string='Nuevo Saldo', default=0.0)
    
    
    _depends = {
        'account.move.line': [
            'company_id', 'balance', 
            'debit', 'credit',
        ],
    }

    @api.model
    def _select(self,date_filter):
        return '''
            SELECT
                Row_Number() Over(Order By G.id,D.Cuenta_Nivel_5,C.display_name) as id,
                G.id as company_id,                
                D.Cuenta_Nivel_1 as account_level_one,
                D.Cuenta_Nivel_2 as account_level_two,
                D.Cuenta_Nivel_3 as account_level_three,
                D.Cuenta_Nivel_4 as account_level_four,
                D.Cuenta_Nivel_5 as account_level_five,                
                C.vat || ' | ' || C.display_name as partner,
                COALESCE(E.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(E.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
        ''' % (date_filter,date_filter,date_filter,date_filter)

    @api.model
    def _from(self,date_filter):
        return '''
            FROM account_move_line B
            INNER JOIN res_partner C on B.partner_id = C.id            
            INNER JOIN (
                            SELECT 
                            COALESCE(e.code_prefix,substring(a.code for 1)) as Cuenta_Nivel_1,
                            COALESCE(d.code_prefix,coalesce(c.code_prefix,coalesce(b.code_prefix,substring(a.code for 1)))) || ' - ' || coalesce(d."name",coalesce(c."name",coalesce(b."name",'')))  as Cuenta_Nivel_2,
                            COALESCE(c.code_prefix,coalesce(b.code_prefix,substring(a.code for 1))) || ' - ' || coalesce(c."name",coalesce(b."name",'')) as Cuenta_Nivel_3,
                            COALESCE(b.code_prefix,substring(a.code for 1)) || ' - ' || COALESCE(b."name",a."name") as Cuenta_Nivel_4,
                            a.code || ' - ' || a."name" as Cuenta_Nivel_5,a.id 
                            FROM account_account a
                            LEFT JOIN account_group b on a.group_id = b.id
                            LEFT JOIN account_group c on b.parent_id = c.id
                            LEFT JOIN account_group d on c.parent_id = d.id
                            LEFT JOIN account_group e on d.parent_id = e.id
                        ) D on B.account_id = D.id            
            INNER JOIN res_company G on B.company_id = G.id
            LEFT JOIN (
                        SELECT partner_id,account_id,
                                SUM(debit - credit) as saldo_ant 
                        FROM account_move_line 
                        WHERE "date" < '%s' group by partner_id,account_id
                      ) as E on C.id = E.partner_id and D.id = E.account_id
        ''' % (date_filter,)

    @api.model
    def _where(self):
        return '''
            WHERE  B.parent_state = 'posted'
        '''

    @api.model
    def _group_by(self):
        return '''
            GROUP BY
                G.id,
                D.Cuenta_Nivel_1,
                D.Cuenta_Nivel_2,
                D.Cuenta_Nivel_3,
                D.Cuenta_Nivel_4,
                D.Cuenta_Nivel_5,
                C.vat,
                C.display_name,
                E.saldo_ant
        '''
    
    def init(self):
        
        #Obtener filtro
        if self.env.context.get('date_filter', False):
            date_filter = self.env.context.get('date_filter')
        else:
            date_filter = '2020-01-01'
        
        #Ejecutar Query
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s %s
            )
        ''' % (
            self._table, self._select(date_filter), self._from(date_filter), self._where(), self._group_by()
        ))

    