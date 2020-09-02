# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from functools import lru_cache


class AccountAuxiliarFilter(models.TransientModel):
    _name = "account.auxiliar.filter"
    _description = "Filter - Auxiliar Report"
    
    date_initial = fields.Date(string='Fecha Inicial', required=True) 
    date_finally = fields.Date(string='Fecha Final', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', domain=[('x_type_thirdparty', 'not in', [2])])
    account_one = fields.Char(string='Cuenta 1')
    account_two = fields.Char(string='Cuenta 2')
    account_three = fields.Char(string='Cuenta 3')
    #account_id = fields.Many2one('account.account', string='Cuenta')
    #account_company = fields.Many2one(string='Compañia de la cuenta', readonly=True, related='account_id.company_id', change_default=True)    
    
    def name_get(self):
        result = []
        filters = ''
        for record in self:    
            if record.partner_id:
                filters = record.partner_id.name
            if record.account_one:
                filters = filters +' | Cuenta: '+ record.account_one
            if record.account_two:
                filters = filters +', '+ record.account_two
            if record.account_three:
                filters = filters +', '+ record.account_three
            
            result.append((record.id, "{} | Fecha Inicial: {} - Fecha Final: {}".format(filters,record.date_initial,record.date_finally)))
        return result
    
    def open_pivot_view(self):
        ctx = self.env.context.copy()
        
        if not self.partner_id:
            partner_id = 0
        else:
            partner_id = self.partner_id.id
            
        if not self.account_one:
            account_one = 0
        else:
            account_one = self.account_one
        
        if not self.account_two:
            account_two = 0
        else:
            account_two = self.account_two
        
        if not self.account_three:
            account_three = 0
        else:
            account_three = self.account_three
        
        if account_one == 0 and partner_id == 0:
            raise UserError(_('Debe seleccionar algún filtro de Cliente y/o Cuenta.'))
        
        ctx.update({'date_initial':self.date_initial,'date_finally':self.date_finally,'partner_id':partner_id,
                        'account_one':account_one,'account_two':account_two,'account_three':account_three})
        self.env['account.auxiliar.report'].with_context(ctx).init(),
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pivot Auxiliar',
            'res_model': 'account.auxiliar.report',
            'domain': [],
            'view_mode': 'pivot',
            'context': ctx
        }
    
class AccountAuxiliarReport(models.Model):
    _name = "account.auxiliar.report"
    _description = "Report - Auxiliar"
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
    # Movimiento
    move = fields.Char(string='Movimiento', readonly=True)
    move_name = fields.Char(string='Factura', readonly=True)
    move_date = fields.Date(string='Fecha', readonly=True)
    move_ref = fields.Char(string='Referencia', readonly=True)
    move_budget_group = fields.Char(string='Grupo presupuestal', readonly=True)
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
            Select Row_Number() Over(Order By company_id,account_level_five,partner,move_date) as id,
                    company_id,
                    account_level_one,account_level_two,account_level_three,account_level_four,account_level_five,
                    partner,"move",move_name,move_date,move_ref,move_budget_group,
                    Sum(initial_balance) as initial_balance,Sum(debit) as debit,Sum(credit) as credit,Sum(new_balance) as new_balance
            From
            (
            SELECT
                G.id as company_id,                
                D.Cuenta_Nivel_1 as account_level_one,
                D.Cuenta_Nivel_2 as account_level_two,
                D.Cuenta_Nivel_3 as account_level_three,
                D.Cuenta_Nivel_4 as account_level_four,
                D.Cuenta_Nivel_5 as account_level_five,                
                COALESCE(C.vat || ' | ' || C.display_name,'Tercero Vacio') as partner,
                case when B."date"<'%s' then 'AA_SALDO INICIAL' else 'Factura: ' || B.move_name || ' | Fecha: ' || B."date" || ' | Referencia: ' || B."ref" || ' | Grupo presupuestal: ' || coalesce(h."name",'-') end as move,                   case when B."date"<'%s' then 'AA_SALDO INICIAL' else  B.move_name end as move_name,
                case when B."date"<'%s' then CAST('%s' AS DATE) - CAST('1 days' AS INTERVAL) else  B."date" end as move_date,
                case when B."date"<'%s' then 'AA_SALDO INICIAL' else  B."ref" end as move_ref,
                case when B."date"<'%s' then 'AA_SALDO INICIAL' else coalesce(h."name",'-') end as move_budget_group,
                COALESCE(E.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(E.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
        ''' % (date_filter,date_filter,date_filter,date_filter,date_filter,date_filter,date_filter,date_filter,date_filter,date_filter)

    @api.model
    def _from(self,date_filter):
        return '''
            FROM account_move_line B
            LEFT JOIN res_partner C on B.partner_id = C.id            
            LEFT JOIN (
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
            LEFT JOIN logyca_budget_group H on b.x_budget_group = h.id
            LEFT JOIN (
                        SELECT partner_id,account_id,move_id,
                                SUM(debit - credit) as saldo_ant 
                        FROM account_move_line 
                        WHERE "date" < '%s' and parent_state = 'posted' group by partner_id,account_id,move_id                      
                      ) as E on COALESCE(B.partner_id,0) = COALESCE(E.partner_id,0) and D.id = E.account_id and B.move_id = E.move_id
        ''' % (date_filter,)

    @api.model
    def _where(self,date_filter,partner_id,account_one,account_two,account_three):
        
        where = ''
        
        #Cuando solo filtran cliente
        if partner_id != 0 and account_one == 0:
            where = '''
                        WHERE  B.parent_state = 'posted' and B."date" <= '%s' 
                                and COALESCE(B.partner_id,0) = case when %s = 0 then COALESCE(B.partner_id,0) else %s end                                
                    '''  % (date_filter,partner_id,partner_id)
        
        #Cuando filtran cliente o una sola cuenta
        if account_one != 0:
            where = '''
                        WHERE  B.parent_state = 'posted' and B."date" <= '%s' 
                                and COALESCE(B.partner_id,0) = case when %s = 0 then COALESCE(B.partner_id,0) else %s end                                
                                and D.Cuenta_Nivel_5 like '%s%s'                                
                    '''  % (date_filter,partner_id,partner_id,account_one,'%')
            
        #Cuando filtran cliente o dos cuentas        
        if account_one != 0 and account_two!=0:
            where = '''
                        WHERE  B.parent_state = 'posted' and B."date" <= '%s' 
                                and COALESCE(B.partner_id,0) = case when %s = 0 then COALESCE(B.partner_id,0) else %s end                                
                                and (D.Cuenta_Nivel_5 like '%s%s' or D.Cuenta_Nivel_5 like '%s%s')
                    '''  % (date_filter,partner_id,partner_id,account_one,'%',account_two,'%')
            
        #Cuando filtran cliente o tres cuentas
        if account_one != 0 and account_two!=0 and account_three!=0:
            where = '''
                        WHERE  B.parent_state = 'posted' and B."date" <= '%s' 
                                and COALESCE(B.partner_id,0) = case when %s = 0 then COALESCE(B.partner_id,0) else %s end                                
                                and (D.Cuenta_Nivel_5 like '%s%s' or D.Cuenta_Nivel_5 like '%s%s' or D.Cuenta_Nivel_5 like '%s%s')
                    '''  % (date_filter,partner_id,partner_id,account_one,'%',account_two,'%',account_three,'%')
            
        return where

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
                    B.move_name,
                    B."date",
                    B."ref",
                    H."name",
                    E.saldo_ant
            ) as A
            GROUP BY
                    company_id,
                    account_level_one,account_level_two,account_level_three,account_level_four,account_level_five,
                    partner,"move",move_name,move_date,move_ref,move_budget_group
        '''
    
    def init(self):
        
        #Obtener filtro
        if self.env.context.get('date_initial', False) and self.env.context.get('date_finally', False):
            date_initial = self.env.context.get('date_initial') 
            date_finally = self.env.context.get('date_finally')   
            partner_id = self.env.context.get('partner_id') 
            account_one = self.env.context.get('account_one')  
            account_two = self.env.context.get('account_two')  
            account_three = self.env.context.get('account_three')  
        else:
            date_initial = '2020-01-01'
            date_finally = '2020-02-01'
            partner_id = 0
            account_one = 0
            account_two = 0
            account_three = 0
        
        #Ejecutar Query        
        #Query = '''            
        #        %s %s %s %s            
        #''' % (self._select(date_initial), self._from(date_initial), self._where(date_finally,partner_id,account_id), self._group_by())
        
        #raise ValidationError(_(Query))                
        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s %s
            )
        ''' % (
            self._table, self._select(date_initial), self._from(date_initial), self._where(date_finally,partner_id,account_one,account_two,account_three), self._group_by()
        ))

    