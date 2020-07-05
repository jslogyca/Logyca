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
    account_id = fields.Many2one('account.account', string='Cuenta')
    account_company = fields.Many2one(string='Compañia de la cuenta', readonly=True, related='account_id.company_id', change_default=True)    
    
    def name_get(self):
        result = []
        filters = ''
        for record in self:    
            if record.partner_id:
                filters = record.partner_id.name
            if record.account_id:
                filters = filters +' | Cuenta: '+ record.account_id.code           
            
            result.append((record.id, "{} | Fecha Inicial: {} - Fecha Final: {}".format(filters,record.date_initial,record.date_finally)))
        return result
    
    def open_pivot_view(self):
        ctx = self.env.context.copy()
        
        if not self.partner_id:
            partner_id = 0
        else:
            partner_id = self.partner_id.id
            
        if not self.account_id:
            account_id = 0
        else:
            account_id = self.account_id.id
        
        if account_id == 0 and partner_id == 0:
            raise UserError(_('Debe seleccionar algún filtro de Cliente y/o Cuenta.'))
        
        ctx.update({'date_initial':self.date_initial,'date_finally':self.date_finally,'partner_id':partner_id,'account_id':account_id})
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
                Row_Number() Over(Order By G.id,D.Cuenta_Nivel_5,C.display_name,B."date") as id,
                G.id as company_id,                
                D.Cuenta_Nivel_1 as account_level_one,
                D.Cuenta_Nivel_2 as account_level_two,
                D.Cuenta_Nivel_3 as account_level_three,
                D.Cuenta_Nivel_4 as account_level_four,
                D.Cuenta_Nivel_5 as account_level_five,                
                C.vat || ' | ' || C.display_name as partner,
                'Factura: ' || B.move_name || ' | Fecha: ' || B."date" || ' | Referencia: ' || B."ref" as move,                
                B.move_name as move_name,B."date" as move_date,B."ref" as move_ref,
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
    def _where(self,date_filter,partner_id,account_id):
        return '''
            WHERE  B.parent_state = 'posted' and B."date" < '%s' 
                    and B.partner_id = case when %s = 0 then B.partner_id else %s end
                    and B.account_id = case when %s = 0 then B.account_id else %s end
        '''  % (date_filter,partner_id,partner_id,account_id,account_id)

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
                E.saldo_ant
        '''
    
    def init(self):
        
        #Obtener filtro
        if self.env.context.get('date_initial', False) and self.env.context.get('date_finally', False):
            date_initial = self.env.context.get('date_initial') 
            date_finally = self.env.context.get('date_finally')   
            partner_id = self.env.context.get('partner_id') 
            account_id = self.env.context.get('account_id') 
        else:
            date_initial = '2020-01-01'
            date_finally = '2020-02-01'
            partner_id = 1
            account_id = 1
        
        #Ejecutar Query        
        #Query = '''            
        #        %s %s %s %s            
        #''' % (self._select(date_initial), self._from(date_initial), self._where(date_finally), self._group_by())
        
        #raise ValidationError(_(Query))                
        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s %s
            )
        ''' % (
            self._table, self._select(date_initial), self._from(date_initial), self._where(date_finally,partner_id,account_id), self._group_by()
        ))

    