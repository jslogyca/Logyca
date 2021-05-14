# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date
from functools import lru_cache

class AccountAgedPartner(models.AbstractModel):
    _inherit = "account.aged.partner"


    def _get_columns_name(self, options):
        columns = [
            {},
            {'name': _("Ref"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Due Date"), 'class': 'date', 'style': 'white-space:nowrap;'},
            {'name': _("Journal"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("Account"), 'class': '', 'style': 'text-align:center; white-space:nowrap;'},
            {'name': _("As of: %s") % format_date(self.env, options['date']['date_to']), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("1 - 30"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("31 - 60"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("61 - 90"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("91 - 120"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Older"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
            {'name': _("Total"), 'class': 'number sortable', 'style': 'white-space:nowrap;'},
        ]
        return columns  

    @api.model
    def _get_lines(self, options, line_id=None):
        sign = -1.0 if self.env.context.get('aged_balance') else 1.0
        lines = []
        account_types = [self.env.context.get('account_type')]
        context = {'include_nullified_amount': True}
        if line_id and 'partner_' in line_id:
            # we only want to fetch data about this partner because we are expanding a line
            context.update(partner_ids=self.env['res.partner'].browse(int(line_id.split('_')[1])))
        results, total, amls = self.env['report.account.report_agedpartnerbalance'].with_context(**context)._get_partner_move_lines(account_types, self._context['date_to'], 'posted', 30)

        for values in results:
            vals = {
                'id': 'partner_%s' % (values['partner_id'],),
                'name': values['name'],
                'level': 2,
                'columns': [{'name': ''}] * 4 + [{'name': self.format_value(sign * v), 'no_format': sign * v}
                                                 for v in [values['direction'], values['4'],
                                                           values['3'], values['2'],
                                                           values['1'], values['0'], values['total']]],
                'trust': values['trust'],
                'unfoldable': True,
                'unfolded': 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'),
                'partner_id': values['partner_id'],
            }
            lines.append(vals)
            if 'partner_%s' % (values['partner_id'],) in options.get('unfolded_lines'):
                for line in amls[values['partner_id']]:
                    aml = line['line']
                    if aml.move_id.is_purchase_document():
                        caret_type = 'account.invoice.in'
                    elif aml.move_id.is_sale_document():
                        caret_type = 'account.invoice.out'
                    elif aml.payment_id:
                        caret_type = 'account.payment'
                    else:
                        caret_type = 'account.move'

                    #getting currency
                    currency = aml.move_id.currency_id.name    

                    line_date = aml.date_maturity or aml.date
                    if not self._context.get('no_format'):
                        line_date = format_date(self.env, line_date)
                    vals = {
                        'id': aml.id,
                        'name': aml.move_id.name,
                        'class': 'date',
                        'caret_options': caret_type,
                        'level': 4,
                        'parent_id': 'partner_%s' % (values['partner_id'],),
                        'columns': [{'name': v} for v in [aml.ref, format_date(self.env, aml.date_maturity or aml.date), aml.journal_id.code, aml.account_id.display_name]] +
                                   [{'name': self.format_value(sign * v, blank_if_zero=True), 'no_format': sign * v} for v in [line['period'] == 6-i and line['amount'] or 0 for i in range(7)]],
                        'action_context': {
                            'default_type': aml.move_id.type,
                            'default_journal_id': aml.move_id.journal_id.id,
                        },
                        'title_hover': self._format_aml_name(aml.name, currency, aml.move_id.name),
                    }
                    lines.append(vals)
        if total and not line_id:
            total_line = {
                'id': 0,
                'name': _('Total'),
                'class': 'total',
                'level': 2,
                'columns': [{'name': ''}] * 4 + [{'name': self.format_value(sign * v), 'no_format': sign * v} for v in [total[6], total[4], total[3], total[2], total[1], total[0], total[5]]],
            }
            lines.append(total_line)
        return lines          


class AccountBalancePartnerFilter(models.TransientModel):
    _name = "account.balance.partner.filter"
    _description = "Filter - Balance Partner"
    
    #date_filter = fields.Date(string='Fecha', required=True)
    x_type_filter = fields.Selection([
                                        ('1', 'Periodo'),
                                        ('2', 'Rango de periodos'),
                                        ('3', 'Anual')        
                                    ], string='Tipo', required=True, default='1')    
    x_ano_filter = fields.Integer(string='Año', required=True)
    x_month_filter = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes')
    x_ano_filter_two = fields.Integer(string='Año 2')
    x_month_filter_two = fields.Selection([
                                        ('1', 'Enero'),
                                        ('2', 'Febrero'),
                                        ('3', 'Marzo'),
                                        ('4', 'Abril'),
                                        ('5', 'Mayo'),
                                        ('6', 'Junio'),
                                        ('7', 'Julio'),
                                        ('8', 'Agosto'),
                                        ('9', 'Septiembre'),
                                        ('10', 'Octubre'),
                                        ('11', 'Noviembre'),
                                        ('12', 'Diciembre')        
                                    ], string='Mes 2')
    company_id = fields.Many2one('res.company', string='Compañia')
    
    def name_get(self):
        result = []
        for record in self:
            type = ''
            if record.x_type_filter == '1':
                type = 'Periodo'
            elif record.x_type_filter == '2':
                type = 'Rango de periodos'
            else:
                type = 'Anual'
            
            if record.x_type_filter == '2':
                result.append((record.id, "{} - Inicial: {}-{} | Final: {}-{} ".format(type,record.x_ano_filter,record.x_month_filter,record.x_ano_filter_two,record.x_month_filter_two)))
            elif record.x_type_filter == '3':
                result.append((record.id, "{} - Año: {} | Mes: {}".format(type,record.x_ano_filter,'Enero')))
            else:
                result.append((record.id, "{} - Año: {} | Mes: {}".format(type,record.x_ano_filter,record.x_month_filter)))
        return result
    
    def open_pivot_view(self):
        if not self.company_id:
            company_id = 0
        else:
            company_id = self.company_id.id
        
        ctx = self.env.context.copy()
        ctx.update({'x_type':self.x_type_filter,'x_ano':self.x_ano_filter,'x_month':self.x_month_filter,'x_ano_two':self.x_ano_filter_two,'x_month_two':self.x_month_filter_two,'company_id':company_id})
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
                Row_Number() Over(Order By G.id,D.Cuenta_Nivel_1,D.Cuenta_Nivel_2,D.Cuenta_Nivel_3,D.Cuenta_Nivel_4,D.Cuenta_Nivel_5,C.display_name) as id,
                G.id as company_id,                
                D.Cuenta_Nivel_1 as account_level_one,
                D.Cuenta_Nivel_2 as account_level_two,
                D.Cuenta_Nivel_3 as account_level_three,
                D.Cuenta_Nivel_4 as account_level_four,
                D.Cuenta_Nivel_5 as account_level_five,                
                COALESCE(C.vat || ' | ' || C.display_name,'Tercero Vacio') as partner,
                COALESCE(E.saldo_ant,0) as initial_balance,
                SUM(case when B."date" >= '%s' then B.debit else 0 end) as debit,
                SUM(case when B."date" >= '%s' then B.credit else 0 end) as credit,
                COALESCE(E.saldo_ant,0)+SUM((case when B."date" >= '%s' then B.debit else 0 end - case when B."date" >= '%s' then B.credit else 0 end)) as new_balance
        ''' % (date_filter,date_filter,date_filter,date_filter)

    @api.model
    def _from(self,date_filter):
        return '''
            FROM account_move_line B
            LEFT JOIN res_partner C on B.partner_id = C.id            
            LEFT JOIN (
                            SELECT Cuenta_Nivel_1,Cuenta_Nivel_2,
                                    case when Cuenta_Nivel_2 = Cuenta_Nivel_3 then Cuenta_Nivel_4 else Cuenta_Nivel_3 end as Cuenta_Nivel_3,
                                    Cuenta_Nivel_4,Cuenta_Nivel_5,id
                            From
                            (
                            SELECT 
                            COALESCE(e.code_prefix,substring(a.code for 1)) as Cuenta_Nivel_1,
                            COALESCE(d.code_prefix,coalesce(c.code_prefix,coalesce(b.code_prefix,substring(a.code for 1)))) || ' - ' || coalesce(d."name",coalesce(c."name",coalesce(b."name",a."name")))  as Cuenta_Nivel_2,
                            COALESCE(c.code_prefix,coalesce(b.code_prefix,substring(a.code for 1))) || ' - ' || coalesce(c."name",coalesce(b."name",a."name")) as Cuenta_Nivel_3,
                            COALESCE(b.code_prefix,substring(a.code for 1)) || ' - ' || COALESCE(b."name",a."name") as Cuenta_Nivel_4,
                            a.code || ' - ' || a."name" as Cuenta_Nivel_5,a.id 
                            FROM account_account a
                            LEFT JOIN account_group b on a.group_id = b.id
                            LEFT JOIN account_group c on b.parent_id = c.id
                            LEFT JOIN account_group d on c.parent_id = d.id
                            LEFT JOIN account_group e on d.parent_id = e.id
                            ) as A
                        ) D on B.account_id = D.id            
            INNER JOIN res_company G on B.company_id = G.id
            LEFT JOIN (
                        SELECT partner_id,account_id,
                                SUM(debit - credit) as saldo_ant 
                        FROM account_move_line 
                        WHERE "date" < '%s' and parent_state = 'posted' group by partner_id,account_id
                      ) as E on COALESCE(B.partner_id,0) = COALESCE(E.partner_id,0) and D.id = E.account_id
        ''' % (date_filter,)

    @api.model
    def _where(self,date_filter,company_id):
        return '''
            WHERE  B.parent_state = 'posted' and B."date" < '%s'
            and COALESCE(B.company_id,0) = case when %s = 0 then COALESCE(B.company_id,0) else %s end                                
        '''  % (date_filter,company_id,company_id)

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
        if self.env.context.get('x_type', False) and self.env.context.get('x_ano', False) and self.env.context.get('x_month', False):
            x_type = self.env.context.get('x_type') 
            x_ano = self.env.context.get('x_ano')
            x_month = int(self.env.context.get('x_month'))
            x_ano_two = self.env.context.get('x_ano_two')
            x_month_two = int(self.env.context.get('x_month_two'))
            company_id = self.env.context.get('company_id')
        else:
            x_type = '1'
            x_ano = 2020
            x_month = 1
            x_ano_two = 2020
            x_month_two = 1
            company_id = 0
        
        #Armar fecha dependiendo el tipo seleccionado
        date_filter = ''
        date_filter_next = ''
        
        # Periodo
        if x_type == '1': 
            date_filter = str(x_ano)+'-'+str(x_month)+'-01'    
            
            if x_month == 12:
                x_ano = x_ano + 1 
                x_month = 1
            else:
                x_month = str(int(x_month) + 1)

            date_filter_next = str(x_ano)+'-'+str(x_month)+'-01'
        
        # Rando de periodos
        if x_type == '2': 
            date_filter = str(x_ano)+'-'+str(x_month)+'-01'
            
            if x_month_two == 12:
                x_ano_two = x_ano_two + 1 
                x_month_two = 1
            else:
                x_month_two = str(int(x_month_two) + 1)

            date_filter_next = str(x_ano_two)+'-'+str(x_month_two)+'-01'
            
        # Anual
        if x_type == '3': 
            date_filter = str(x_ano)+'-01-01'            
            
            if x_month == 12:
                x_ano = x_ano + 1 
                x_month = 1
            else:
                x_month = str(int(x_month) + 1)

            date_filter_next = str(x_ano)+'-'+str(x_month)+'-01'
        
                
        #Ejecutar Query        
        #Query = '''            
        #        %s %s %s %s            
        #''' % (self._select(date_filter), self._from(date_filter), self._where(date_filter_next), self._group_by())
        
        #raise ValidationError(_(Query))                
        
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                %s %s %s %s
            )
        ''' % (
            self._table, self._select(date_filter), self._from(date_filter), self._where(date_filter_next,company_id), self._group_by()
        ))

    
