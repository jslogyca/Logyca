from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta
from pytz import timezone

import pandas as pd
import base64
import io
import xlsxwriter
import odoo
import threading
import math
import logging
import gc
import os
import time

_logger = logging.getLogger(__name__)

class account_auxiliary_report_filters(models.TransientModel):
    _name = "account.auxiliary.report.filters"
    _description = "Filtros - Reporte auxiliar contabilidad"

    company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
    date_start = fields.Date(string='Fecha inicial', required=True)
    date_end = fields.Date(string='Fecha final', required=True)
    type_auxiliary = fields.Selection([
        ('1', 'Por Cuenta Contable'),
        ('2', 'Por Cuenta Contable - Tercero'),
        #('2.1', 'Por Tercero - Cuenta Contable'),
        #('3', 'Por Cuenta Contable – Cuenta Analítica'),
        #('3.1', 'Por Cuenta Analítica - Cuenta Contable'),
        ('4', 'Por Cuenta Contable - Tercero - Cuenta Analítica')
    ], string='Tipo de auxiliar', default='1')
    #Filtros
    #--Cuentas
    filter_show_only_terminal_accounts = fields.Boolean(string='Mostrar solo cuentas terminales')
    filter_exclude_auxiliary_test = fields.Boolean(string='Excluir cuentas parametrizadas')
    filter_accounting_class = fields.Char(string='Clase')
    filter_account_ids = fields.Many2many('account.account', string="Cuentas terminales")
    filter_account_group_ids = fields.Many2many('account.group', string="Cuentas mayores")
    filter_higher_level = fields.Selection([
        ('1', '1'),('2', '2'),('3', '3'),
        ('4', '4'), ('5', '5'), ('6', '6'),
        ('7', '7'), ('8', '8'), ('9', '9')
    ], string='Nivel')
    # --Terceros
    filter_partner_ids = fields.Many2many('res.partner', string="Terceros")
    # --Cuentas Analíticas
    filter_account_analytic_group_ids = fields.Many2many('account.analytic.group', string="Cuentas analíticas mayores")
    filter_account_analytic_ids = fields.Many2many('account.analytic.account', string="Cuentas analíticas terminales")
    filter_show_only_terminal_account_analytic = fields.Boolean(string='Mostrar solo cuentas analíticas terminales')
    filter_higher_level_analytic = fields.Selection([
        ('1', '1'), ('2', '2'), ('3', '3'),
        ('4', '4'), ('5', '5'), ('6', '6'),
        ('7', '7'), ('8', '8'), ('9', '9')
    ], string='Nivel Analítico')
    # --Diarios
    filter_account_journal_ids = fields.Many2many('account.journal', string="Diarios Excluidos")
    #Cierre de año
    filter_with_close = fields.Boolean(string='Con cierre', default=True)
    #Guardar excel
    excel_file = fields.Binary('Excel file')
    excel_file_name = fields.Char('Excel name')
    #Html
    preview = fields.Html('Reporte Preview')

    def name_get(self):
        result = []
        for record in self:
            period_txt = f'PERIODO {self.date_start} a {self.date_end}'
            type_auxiliary_txt = dict(self._fields['type_auxiliary'].selection).get(self.type_auxiliary)
            name_get = f'Auxiliar {period_txt.lower()} {type_auxiliary_txt}'
            result.append((record.id, name_get))
        return result

    def generate_report_html(self):
        html = self.generate_report(1)
        self.write({'preview': html})
        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.auxiliary.report.filters',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def generate_report(self,return_html=0):
        date_start = self.date_start
        date_end = self.date_end
        #-----------------------------Filtros necesarios para obtener la información----------------------------------
        query_where = f"where b.company_id = {self.company_id.id} and a.parent_state = 'posted' and a.date <= '{date_end}' "
        #domain = [('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'), ('date', '<=', date_end)]
        # --Terceros
        if len(self.filter_partner_ids) > 0 and self.type_auxiliary in ('2','2.1'):
            query_where += f"\n and a.partner_id in {str(self.filter_partner_ids.ids).replace('[', '(').replace(']', ')')} "
            #domain.append(('partner_id', 'in', self.filter_partner_ids.ids))
        # --Cuentas Analíticas
        if len(self.filter_account_analytic_ids) > 0 and self.type_auxiliary in ('3', '3.1'):
            query_where += f"\n and a.analytic_distribution ->>'id' in {str(self.filter_account_analytic_ids.ids).replace('[', '(').replace(']', ')')} "
            query_where_t += f"\n and a.analytic_distribution ->>'id' in {str(self.filter_account_analytic_ids.ids).replace('[', '(').replace(']', ')')} "
        if len(self.filter_account_analytic_group_ids) > 0:  # Cuentas analiticas mayores
            raise ValidationError('El filtro de cuentas analiticas mayores esta en desarrollo.')
            # No se puede hacer con la nueva versión del balance que es con consulta SQL
            #domain.append(('analytic_account_id.group_id', 'child_of', self.filter_account_analytic_group_ids.ids))
        # --Excluir Diarios
        if len(self.filter_account_journal_ids) > 0:
            query_where += f"\n and a.journal_id not in {str(self.filter_account_journal_ids.ids).replace('[', '(').replace(']', ')')} "
            #domain.append(('journal_id','not in',self.filter_account_journal_ids.ids))
        # --Cuentas
        if self.filter_accounting_class:  # Clase
            query_where += f"\n and c.accounting_class = '{self.filter_accounting_class}' "
            #domain.append(('account_id.accounting_class', '=', self.filter_accounting_class))
        if len(self.filter_account_ids) > 0:  # Cuentas terminales
            query_where += f"\n and a.account_id in {str(self.filter_account_ids.ids).replace('[', '(').replace(']', ')')} "
            #domain.append(('account_id', 'in', self.filter_account_ids.ids))
        if len(self.filter_account_group_ids) > 0:  # Cuentas mayores
            query_where += '\n and ('
            j = len(self.filter_account_group_ids)
            i = 1
            for filter in self.filter_account_group_ids:
                if i == j:
                    query_where += f"c.code like '{filter.code_prefix_start}%'"
                else:
                    query_where += f"c.code like '{filter.code_prefix_start}%' or "
                i += 1
            query_where += ')'
            #domain.append(('account_id.group_id', 'child_of', self.filter_account_group_ids.ids))
        if self.filter_exclude_auxiliary_test:
            query_where += f"\n and (c.exclude_balance_test = false or c.exclude_balance_test is null) "
            #domain.append(('account_id.exclude_auxiliary_test', '=', False))
        #--------------------------------------Filtro de Cierre de Año------------------------------------------------
        if self.filter_with_close == False:
            query_where += f"\n and a.id not in (select a.id from account_move_line as a inner join account_move as b on a.move_id = b.id where a.company_id = {self.company_id.id} and a.parent_state = 'posted' and a.date >= '{datetime.strptime(str(date_end.year) + '-12-01', '%Y-%m-%d').date()}' and b.accounting_closing_id is not null) "
            #domain_close = [('company_id', '=', self.company_id.id), ('parent_state', '=', 'posted'),
            #          ('date', '>=', datetime.strptime(str(date_end.year)+'-12-01', '%Y-%m-%d').date()),('move_id.accounting_closing_id','!=',False)]
            #domain.append(('id', 'not in', self.env['account.move.line'].search(domain_close).ids))
        # --------------------------------LOGICA POR SQL--------------------------------------------------------------
        # Obtener la cantidad de niveles existentes en el plan de cuenta
        obj_account_account = self.env['account.account'].search([])
        lst_levels_group = []
        lst_levels_group_str = []
        df_name_columns_account = []
        for account in obj_account_account:
            i = 1
            have_parent = True
            group_account = account.group_id
            while have_parent:
                if group_account.parent_id:
                    name_in_dict = (i, 'Nivel ' + str(i), 'Nivel ' + str(i) + ' Descripción')
                    group_account = group_account.parent_id
                    if not name_in_dict in lst_levels_group:
                        lst_levels_group.append(name_in_dict)
                        lst_levels_group_str.append('Nivel ' + str(i))
                        df_name_columns_account.append('Nivel ' + str(i))
                        df_name_columns_account.append('Nivel ' + str(i) + ' Descripción')
                        df_name_columns_account.append('Nivel ' + str(i) + ' Tercero')
                        df_name_columns_account.append('Nivel ' + str(i) + ' Cuenta Analítica')
                        df_name_columns_account.append('Nivel ' + str(i) + ' Movimiento')
                        df_name_columns_account.append('Nivel ' + str(i) + ' Fecha')
                        df_name_columns_account.append('Nivel ' + str(i) + ' Concepto')
                    i += 1
                else:
                    have_parent = False
        query_select_levels_group = ''
        query_from_levels_group = ''
        for q_group in lst_levels_group:
            query_select_levels_group += f'c{q_group[0]}.code_prefix_start as "{q_group[1]}", c{q_group[0]}."name" as "{q_group[2]}",'
            query_select_levels_group += f''' ' ' as "Nivel {q_group[0]} Tercero", ' ' as "Nivel {q_group[0]} Cuenta Analítica", ' ' as "Nivel {q_group[0]} Movimiento", ' ' as "Nivel {q_group[0]} Fecha", ' ' as "Nivel {q_group[0]} Concepto", '''
            query_from_levels_group += f'left join account_group as c{q_group[0]} on c{q_group[0] - 1}.parent_id = c{q_group[0]}.id '
        query_select_levels_group = '--NO AHI GRUPOS DE CUENTA' if query_select_levels_group == '' else query_select_levels_group
        query_from_levels_group = '--NO AHI GRUPOS DE CUENTA' if query_from_levels_group == '' else query_from_levels_group
        # Obtener la cantidad de niveles existentes en el plan de cuentas analiticas
        obj_account_analytic_account = self.env['account.analytic.account'].search([])
        lst_levels_group_analytic = []
        lst_levels_group_analytic_str = []
        df_name_columns_analytic = []
        for account_analytic in obj_account_analytic_account:
            j = 1
            have_parent_analytic = True
            group_analytic_account = account_analytic.plan_id
            while have_parent_analytic:
                if group_analytic_account.parent_id:
                    name_in_dict_analytic = (j, 'Nivel Analítica ' + str(j))
                    group_analytic_account = group_analytic_account.parent_id
                    if not name_in_dict_analytic in lst_levels_group_analytic:
                        lst_levels_group_analytic.append(name_in_dict_analytic)
                        lst_levels_group_analytic_str.append('Nivel Analítica ' + str(j))
                        df_name_columns_analytic.append('Nivel Analítica ' + str(j))
                    j += 1
                else:
                    have_parent_analytic = False
        query_select_levels_group_analytic = ''
        query_from_levels_group_analytic = ''
        for q_group_analytic in lst_levels_group_analytic:
            str_empty = 'Cuenta Analítica Vacia'
            query_select_levels_group_analytic += f'''coalesce(e{q_group_analytic[0]}."name",'{str_empty}') as "Nivel Analítica {q_group_analytic[0]}", '''
            query_from_levels_group_analytic += f'left join account_analytic_plan as e{q_group_analytic[0]} on e{q_group_analytic[0] - 1}.parent_id = e{q_group_analytic[0]}.id '
        query_select_levels_group_analytic = '--NO AHI GRUPOS DE CUENTA ANALITICA' if query_select_levels_group_analytic == '' else query_select_levels_group_analytic
        query_from_levels_group_analytic = '--NO AHI GRUPOS DE CUENTA ANALITICA' if query_from_levels_group_analytic == '' else query_from_levels_group_analytic
        # --------------QUERY FINAL
        df_name_columns = df_name_columns_account + ['Nivel 0', 'Nivel 0 Descripción', 'Nivel 0 Tercero',
                                                     'Nivel 0 Cuenta Analítica', 'Nivel 0 Movimiento',
                                                     'Nivel 0 Fecha', 'Nivel 0 Concepto', 'Cuenta',
                                                     'Descripción', 'Tercero']
        df_name_columns = df_name_columns + df_name_columns_analytic
        df_name_columns = df_name_columns + ['Nivel Analítica 0', 'Cuenta Analítica',
                                             'Movimiento', 'Fecha', 'Concepto',
                                             'Saldo Anterior', 'Débito',
                                             'Crédito', 'Nuevo Saldo', 'Total']
        query = f'''
                        Select --Cuenta
                                {query_select_levels_group}
                                c0.code_prefix_start as "Nivel 0", c0."name" as "Nivel 0 Descripción",
                                ' ' as "Nivel 0 Tercero", ' ' as "Nivel 0 Cuenta Analítica",
                                ' ' as "Nivel 0 Movimiento", ' ' as "Nivel 0 Fecha",' ' as "Nivel 0 Concepto",
                                c.code as "Cuenta", c."name" as "Descripción",
                                --Tercero
                                coalesce(case when d.vat is not null then d.vat || ' | ' || d.display_name else d.display_name end,'Tercero Vacio') as "Tercero",
                                --Cuenta Analítica
                                {query_select_levels_group_analytic}
                                coalesce(e0."name",'Cuenta Analítica Vacia') as "Nivel Analítica 0",
                                coalesce(e."name",'Cuenta Analítica Vacia') as "Cuenta Analítica",
                                --Información Adicional
                                b."name" as "Movimiento",
                                b.date as "Fecha",
                                a."name" as "Concepto",
                                --Valores
                                case when a."date" < '{date_start}' then a.debit - a.credit
                                    else 0 end as "Saldo Anterior",
                                case when a.date >= '{date_start}' and a.date <= '{date_end}' then a.debit
                                    else 0 end as "Débito",	
                                case when a.date >= '{date_start}' and a.date <= '{date_end}' then a.credit
                                    else 0 end as "Crédito",
                                (case when a."date" < '{date_start}' then a.debit - a.credit else 0 end) + ((case when a.date >= '{date_start}' and a.date <= '{date_end}' then a.debit else 0 end) - (case when a.date >= '{date_start}' and a.date <= '{date_end}' then a.credit else 0 end)) as "Nuevo Saldo",                            
                                '--TOTAL--' as "Total"
                        From account_move_line as a
                        inner join account_move as b on a.move_id = b.id 
                        inner join account_account as c on a.account_id = c.id
                        left join res_partner as d on a.partner_id = d.id  
                        left join account_analytic_account as e on a.analytic_account_id = e.id
                        left join account_group as c0 on c.group_id = c0.id
                        {query_from_levels_group}
                        left join account_analytic_group as e0 on e.group_id = e0.id      
                        {query_from_levels_group_analytic}  
                        {query_where}
                '''
        self.env.cr.execute(query)
        lst_info = self.env.cr.fetchall()
        # Logica Hilos // SE INACTIVA 11/09/2023
        '''
        #----------------------------------------Obtener información--------------------------------------------------
        obj_moves = self.env['account.move.line'].search(domain)
        div = 10000
        moves_array, i, j = [], 0, div
        if len(obj_moves) == 0:
            raise ValidationError(_('No se encontro información con los filtros seleccionados, por favor verificar.'))
        while i <= len(obj_moves):
            moves_array.append(obj_moves[i:j])
            i = j
            j += div

        div = 5
        moves_array_def, i, j = [], 0, div
        while i <= len(moves_array):
            moves_array_def.append(moves_array[i:j])
            i = j
            j += div
        # ----------------------------Recorrer información por multihilos
        def get_dict_moves(moves_ids):
            with odoo.api.Environment.manage():
                registry = odoo.registry(self._cr.dbname)
                with registry.cursor() as cr:
                    env = api.Environment(cr, SUPERUSER_ID, {})
                    moves = env['account.move.line'].search([('id','in',moves_ids)])
                    for move in moves:
                        group_account, have_parent, i, dict_levels_account, dict_initial = move.account_id.group_id, True, 1, {}, {}
                        group_analytic_account, have_parent_analytic, j, dict_levels_analytic_account = move.analytic_account_id.group_id, True, 1, {}
                        # Validar cuantos niveles posee esta cuenta contable
                        while have_parent:
                            if group_account.parent_id:
                                name_in_dict = 'Nivel ' + str(i)
                                dict_levels_account[name_in_dict] = group_account.parent_id.code_prefix
                                dict_levels_account[name_in_dict + ' Descripción'] = group_account.parent_id.name
                                dict_levels_account[name_in_dict + ' Tercero'] = ' '
                                dict_levels_account[name_in_dict + ' Cuenta Analítica'] = ' '
                                dict_levels_account[name_in_dict + ' Movimiento'] = ' '
                                dict_levels_account[name_in_dict + ' Fecha'] = ' '
                                dict_levels_account[name_in_dict + ' Concepto'] = ' '
                                group_account = group_account.parent_id
                                i += 1
                                if not name_in_dict in lst_levels_group:
                                    lst_levels_group.append(name_in_dict)
                            else:
                                have_parent = False

                        while have_parent_analytic:
                            if group_analytic_account.parent_id:
                                name_in_dict_analytic = 'Nivel Analítica ' + str(j)
                                dict_levels_analytic_account[name_in_dict_analytic] = group_analytic_account.parent_id.display_name
                                group_analytic_account = group_analytic_account.parent_id
                                j += 1
                                if not name_in_dict_analytic in lst_levels_group_analytic:
                                    lst_levels_group_analytic.append(name_in_dict_analytic)
                            else:
                                have_parent_analytic = False

                        # Diccionario principal
                        initial_auxiliary = move.debit - move.credit if move.date < date_start else 0
                        debit = move.debit if move.date >= date_start and move.date <= date_end else 0
                        credit = move.credit if move.date >= date_start and move.date <= date_end else 0
                        new_auxiliary = initial_auxiliary + (debit - credit)
                        dict_initial = {
                            'Nivel 0': move.account_id.group_id.code_prefix,
                            'Nivel 0 Descripción': move.account_id.group_id.name,
                            'Nivel 0 Tercero': ' ',
                            'Nivel 0 Cuenta Analítica': ' ',
                            'Nivel 0 Movimiento': ' ',
                            'Nivel 0 Fecha': ' ',
                            'Nivel 0 Concepto': ' ',
                            'Cuenta': move.account_id.code,
                            'Descripción': move.account_id.name,
                            'Tercero': move.partner_id.vat + '|' + move.partner_id.display_name if move.partner_id else 'Tercero Vacio',
                            'Nivel Analítica 0': move.analytic_account_id.group_id.display_name if move.analytic_account_id else 'Cuenta Analítica Vacia',
                            'Cuenta Analítica': move.analytic_account_id.group_id.display_name+' / '+move.analytic_account_id.display_name if move.analytic_account_id else 'Cuenta Analítica Vacia',
                            'Movimiento': move.move_id.name,
                            'Fecha': str(move.move_id.date),
                            'Concepto': move.name,
                            'Saldo Anterior': initial_auxiliary,
                            'Débito': debit,
                            'Crédito': credit,
                            'Nuevo Saldo': new_auxiliary,
                            'Total': '--TOTAL--',  # Se crea esta variable para agrupar por ella y obtener los totales
                        }
                        lst_info.append({**dict_levels_account, **dict_levels_analytic_account,**dict_initial})
                    return

        lst_info, lst_levels_group, lst_levels_group_analytic = [], [], []
        for moves_group in moves_array_def:
            threads = []
            for i_moves in moves_group:
                if len(i_moves) > 0:
                    t = threading.Thread(target=get_dict_moves,args=(i_moves.ids,))
                    threads.append(t)
                    t.start()

            for thread in threads:
                thread.join()
        '''
        # ----------------------------------------DATAFRAMES PANDAS--------------------------------------------------
        lst_levels_group, lst_levels_group_analytic = lst_levels_group_str, lst_levels_group_analytic_str
        if len(lst_info) == 0:
            raise ValidationError(_('No se encontro información con los filtros seleccionados, por favor verificar.'))
        df_report_original = pd.DataFrame.from_dict(lst_info)
        df_report_original = df_report_original.set_axis(df_name_columns, axis=1)
        lst_levels_group = sorted(lst_levels_group,reverse=True)
        lst_levels_group_analytic = sorted(lst_levels_group_analytic, reverse=True)
        #Agrupar información de acuerdo al tipo de auxiliar
        lst_dataframes,lst_group_by,lst_levels_group_by,lst_levels_group_analytic_by = [],[],[],[]
        cant_levels = len(lst_levels_group) + 2 #La cantidad de niveles encontrados + los 2 por defecto
        cant_levels_analytic = len(lst_levels_group_analytic) + 2  # La cantidad de niveles encontrados + los 2 por defecto
        filter_higher_level = int(self.filter_higher_level) if self.filter_higher_level else 9999
        filter_higher_level_analytic = int(self.filter_higher_level_analytic) if self.filter_higher_level_analytic else 9999
        if self.type_auxiliary == '1': # Auxiliar por Cuenta Contable
            lst_group_by = ['Cuenta', 'Descripción','Fecha','Movimiento','Cuenta Analítica','Tercero','Concepto']
            lst_levels_group_by = ['Nivel 0', 'Nivel 0 Descripción','Nivel 0 Fecha','Nivel 0 Movimiento','Nivel 0 Cuenta Analítica','Nivel 0 Tercero','Nivel 0 Concepto']
        elif self.type_auxiliary == '2': # Auxiliar por Cuenta Contable - Tercero
            lst_group_by = ['Cuenta', 'Descripción','Tercero','Fecha','Movimiento','Cuenta Analítica','Concepto']
            lst_levels_group_by = ['Nivel 0', 'Nivel 0 Descripción','Nivel 0 Tercero','Nivel 0 Fecha','Nivel 0 Movimiento','Nivel 0 Cuenta Analítica','Nivel 0 Concepto']
        elif self.type_auxiliary == '2.1': # Auxiliar por Tercero - Cuenta Contable
            lst_group_by = ['Tercero','Cuenta', 'Descripción']
            lst_levels_group_by = ['Tercero','Nivel 0', 'Nivel 0 Descripción']
        elif self.type_auxiliary == '3': # Auxiliar por Cuenta Contable – Cuenta Analítica
            lst_group_by = ['Cuenta', 'Descripción', 'Cuenta Analítica']
            lst_levels_group_by = ['Nivel 0', 'Nivel 0 Descripción', 'Nivel 0 Cuenta Analítica']
            lst_levels_group_analytic_by = ['Cuenta', 'Descripción', 'Nivel Analítica 0']
        elif self.type_auxiliary == '3.1': # Auxiliar por Cuenta Analítica - Cuenta Contable
            lst_group_by = ['Cuenta Analítica','Cuenta', 'Descripción']
            top_analytic = lst_levels_group_analytic[filter_higher_level_analytic-1] if filter_higher_level_analytic <= len(lst_levels_group_analytic) else 'Nivel Analítica 0'
            top_analytic = 'Cuenta Analítica' if filter_higher_level_analytic > len(lst_levels_group_analytic)+1 else top_analytic
            lst_levels_group_by = [top_analytic,'Nivel 0', 'Nivel 0 Descripción']
            lst_levels_group_analytic_by = ['Nivel Analítica 0','Cuenta', 'Descripción']
        elif self.type_auxiliary == '4':  # Auxiliar por Cuenta Contable - Cuenta Analítica - Tercero
            lst_group_by = ['Cuenta', 'Descripción', 'Tercero', 'Cuenta Analítica', 'Fecha', 'Movimiento', 'Concepto']
            lst_levels_group_by = ['Nivel 0', 'Nivel 0 Descripción', 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica', 'Nivel 0 Fecha', 'Nivel 0 Movimiento', 'Nivel 0 Concepto']
            #lst_levels_group_analytic_by = ['Cuenta', 'Descripción', 'Nivel Analítica 0', 'Nivel 0 Tercero']
        df_report = df_report_original.groupby(by=lst_group_by, group_keys=False,as_index=False).sum()
        # Agrupar información niveles cuentas
        lst_agroup_higher_level = []
        if self.filter_show_only_terminal_accounts == False:
            if filter_higher_level >= cant_levels - 1:
                lst_levels_group_by_dinamic = []
                if self.type_auxiliary in ('2', '3', '4') and filter_higher_level == cant_levels - 1:
                    for index, group in enumerate(lst_levels_group_by):
                        lst_agroup_higher_level.append(lst_levels_group_by[index])
                        level_replace = lst_levels_group_by[index] if lst_levels_group_by[index] != 'Nivel 0 Tercero' else 'Tercero'
                        #level_replace = level_replace if lst_levels_group_by[index] != 'Nivel 0 Cuenta Analítica' else 'Cuenta Analítica'
                        lst_levels_group_by_dinamic.append(level_replace)
                else:
                    lst_levels_group_by_dinamic = lst_levels_group_by
                df_level_0 = df_report_original.groupby(by=lst_levels_group_by_dinamic, group_keys=False,as_index=False).sum()
                lst_dataframes.append(df_level_0)
            item_level = 1
            for level in lst_levels_group: #Se recorren los niveles de las cuentas contables y se mayoriza
                if filter_higher_level >= item_level:
                    lst_levels_group_by_dinamic = []
                    for index, group in enumerate(lst_levels_group_by):
                        if self.type_auxiliary in ('2','3', '4') and filter_higher_level == item_level:
                            lst_agroup_higher_level.append(lst_levels_group_by[index].replace('Nivel 0',level))
                            level_replace = lst_levels_group_by[index].replace('Nivel 0', level) if lst_levels_group_by[index] != 'Nivel 0 Tercero' else 'Tercero'
                            #level_replace = level_replace if lst_levels_group_by[index] != 'Nivel 0 Cuenta Analítica' else 'Cuenta Analítica'
                            lst_levels_group_by_dinamic.append(level_replace)
                        else:
                            lst_levels_group_by_dinamic.append(lst_levels_group_by[index].replace('Nivel 0',level))
                    df_level = df_report_original.groupby(by=lst_levels_group_by_dinamic, group_keys=False,as_index=False).sum()
                    lst_dataframes.append(df_level)
                item_level += 1
        # Agrupar información niveles cuentas analíticas cuando el tipo de auxiliar lo requiere
        lst_agroup_higher_level_analytic = []
        if self.filter_show_only_terminal_account_analytic == False and self.type_auxiliary in ('3','3.1'):
            if self.type_auxiliary == '3':
                if filter_higher_level >= cant_levels:
                    lst_dinamic_inherit_account = lst_levels_group_analytic_by
                else:
                    lst_dinamic_inherit_account = [lst_levels_group_by_dinamic[0],lst_levels_group_by_dinamic[1],'Nivel Analítica 0']
                if filter_higher_level_analytic >= cant_levels_analytic - 1:
                    df_level_analytic_0 = df_report_original.groupby(by=lst_dinamic_inherit_account, group_keys=False,
                                                            as_index=False).sum()
                    lst_dataframes.append(df_level_analytic_0)
                item_level = 1
                for level in lst_levels_group_analytic:  # Se recorren los niveles de las cuentas contables y se mayoriza
                    if filter_higher_level_analytic >= item_level:
                        lst_levels_group_by_dinamic = []
                        for index, group in enumerate(lst_dinamic_inherit_account):
                            lst_levels_group_by_dinamic.append(lst_dinamic_inherit_account[index].replace('Nivel Analítica 0', level))
                        df_level = df_report_original.groupby(by=lst_levels_group_by_dinamic, group_keys=False,
                                                              as_index=False).sum()
                        lst_dataframes.append(df_level)
                    item_level += 1
            else:
                if filter_higher_level >= cant_levels:
                    lst_dinamic_inherit_account = ['Nivel Analítica 0', 'Cuenta', 'Descripción']
                else:
                    lst_dinamic_inherit_account = lst_levels_group_by_dinamic
                lst_level_0_group_by_dinamic = ['Nivel Analítica 0', 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica']
                if filter_higher_level_analytic >= cant_levels_analytic - 1:
                    if filter_higher_level_analytic == cant_levels_analytic - 1:
                        lst_level_0_group_by_dinamic = ['Nivel Analítica 0',lst_dinamic_inherit_account[1],lst_dinamic_inherit_account[2]]

                    df_level_analytic_0 = df_report_original.groupby(by=lst_level_0_group_by_dinamic, group_keys=False,
                                                                     as_index=False).sum()
                    lst_dataframes.append(df_level_analytic_0)
                item_level = 1
                lst_level_0_group_by_dinamic = ['Nivel Analítica 0', 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica']
                for level in lst_levels_group_analytic:  # Se recorren los niveles de las cuentas contables y se mayoriza
                    if filter_higher_level_analytic >= item_level:
                        lst_levels_group_by_dinamic = []
                        if filter_higher_level_analytic == item_level:
                            lst_levels_group_by_dinamic = [level,lst_dinamic_inherit_account[1],lst_dinamic_inherit_account[2]]
                        else:
                            for index, group in enumerate(lst_level_0_group_by_dinamic):
                                lst_levels_group_by_dinamic.append(lst_level_0_group_by_dinamic[index].replace('Nivel Analítica 0', level))
                        df_level = df_report_original.groupby(by=lst_levels_group_by_dinamic, group_keys=False,
                                                              as_index=False).sum()
                        lst_dataframes.append(df_level)
                    item_level += 1
        #Agrupar por tipo de auxliar
        if self.type_auxiliary in ['2','3']:
            if filter_higher_level >= cant_levels:  # Si es auxliar con tercero o cuenta analitica se crea la sumatoria de la cuenta contable
                df_tercero = df_report_original.groupby(by=['Cuenta', 'Descripción', 'Tercero', 'Nivel 0 Fecha', 'Nivel 0 Movimiento', 'Nivel 0 Cuenta Analítica', 'Nivel 0 Concepto'], group_keys=False, as_index=False).sum()
                lst_dataframes.append(df_tercero)
                df_account = df_report_original.groupby(by=['Cuenta', 'Descripción', 'Nivel 0 Tercero','Nivel 0 Fecha','Nivel 0 Movimiento','Nivel 0 Cuenta Analítica','Nivel 0 Concepto'],group_keys=False,as_index=False).sum()
                lst_dataframes.append(df_account)
            else:
                df_account = df_report_original.groupby(by=lst_agroup_higher_level,group_keys=False, as_index=False).sum()
                lst_dataframes.append(df_account)
        if self.type_auxiliary in ['2.1']:  # Si es auxliar por tercero - cuenta contable, se crea la sumatoria del tercero
            df_account = df_report_original.groupby(by=['Tercero', 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica'],group_keys=False,as_index=False).sum()
            lst_dataframes.append(df_account)
        if self.type_auxiliary in ['3.1']:  # Si es auxliar por cuenta analitica - cuenta contable, se crea la sumatoria de la cuenta analitica
            df_account = df_report_original.groupby(by=[top_analytic, 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica'], group_keys=False,as_index=False).sum()
            lst_dataframes.append(df_account)
        if self.type_auxiliary in ['4']:  # Si es auxliar por cuenta analitica - cuenta contable, se crea la sumatoria de la cuenta analitica
            if filter_higher_level >= cant_levels:  # Si es auxliar con tercero o cuenta analitica se crea la sumatoria de la cuenta contable
                df_analityc_account = df_report_original.groupby(by=['Cuenta', 'Descripción', 'Tercero', 'Cuenta Analítica', 'Nivel 0 Fecha', 'Nivel 0 Movimiento', 'Nivel 0 Concepto'], group_keys=False, as_index=False).sum()
                lst_dataframes.append(df_analityc_account)
                df_tercero = df_report_original.groupby(by=['Cuenta', 'Descripción', 'Tercero', 'Nivel 0 Cuenta Analítica', 'Nivel 0 Fecha', 'Nivel 0 Movimiento', 'Nivel 0 Concepto'], group_keys=False, as_index=False).sum()
                lst_dataframes.append(df_tercero)
                df_account = df_report_original.groupby(by=['Cuenta', 'Descripción', 'Nivel 0 Tercero', 'Nivel 0 Cuenta Analítica', 'Nivel 0 Fecha', 'Nivel 0 Movimiento', 'Nivel 0 Concepto'], group_keys=False, as_index=False).sum()
                lst_dataframes.append(df_account)
            else:
                df_account = df_report_original.groupby(by=lst_agroup_higher_level, group_keys=False,
                                                        as_index=False).sum()
                lst_dataframes.append(df_account)
        #Concatenar dataframes
        if filter_higher_level >= cant_levels and filter_higher_level_analytic >= cant_levels_analytic:
            lst_dataframes.append(df_report)
        df_report_finally = False
        columns = lst_group_by + ['Saldo Anterior', 'Débito', 'Crédito', 'Nuevo Saldo']
        for df in lst_dataframes:
            df.columns = columns
            if type(df_report_finally) is bool:
                df_report_finally = df
            else:
                df_report_finally = df_report_finally.append(df)
        try:
            df_report_finally = df_report_finally.sort_values(by=lst_group_by)
        except:
            df_report_finally = df_report_finally.sort_values(by=lst_levels_group_by_dinamic)
        #Eliminar elementos de fechas que esta por fuera del reporte
        df_report_finally = df_report_finally.reset_index()
        for i, row in df_report_finally.iterrows():
            if type(df_report_finally.loc[i, 'Fecha']) is str:
                if df_report_finally.loc[i, 'Fecha'] and df_report_finally.loc[i, 'Fecha'] != ' ':
                    if not (datetime.strptime(df_report_finally.loc[i, 'Fecha'],
                                              '%Y-%m-%d').date() >= date_start and datetime.strptime(
                        df_report_finally.loc[i, 'Fecha'], '%Y-%m-%d').date() <= date_end):
                            df_report_finally = df_report_finally.drop(index=[i])
        #Eliminar duplicados para garantizar la información
        df_report_finally = df_report_finally.drop_duplicates()
        #Eliminar filas con todos sus valores en 0
        df_report_finally = df_report_finally[(df_report_finally['Saldo Anterior'] != 0) | (df_report_finally['Débito'] != 0) | (df_report_finally['Crédito'] != 0) | (df_report_finally['Nuevo Saldo'] != 0)]
        #Dataframe totales
        df_total = df_report_original.groupby(by=['Total'], group_keys=False,as_index=False).sum()
        #-------------------------------------------Crear Excel------------------------------------------------------
        if return_html == 0:
            period_txt = f'PERIODO {self.date_start} a {self.date_end}'
            type_auxiliary_txt = dict(self._fields['type_auxiliary'].selection).get(self.type_auxiliary)
            filename = f'Auxiliar {period_txt.lower()} {type_auxiliary_txt}.xlsx'
            stream = io.BytesIO()
            writer = pd.ExcelWriter(stream, engine='xlsxwriter')
            writer.book.filename = stream
            columns = lst_group_by + ['Saldo Anterior', 'Débito', 'Crédito', 'Nuevo Saldo']
            df_report_finally.to_excel(writer, sheet_name='Auxiliar', float_format="%.2f", columns=columns, header=columns, index=False, startrow=4, startcol=0)
            df_total.to_excel(writer, sheet_name='Auxiliar', float_format="%.2f", columns=['Total','Saldo Anterior', 'Débito', 'Crédito', 'Nuevo Saldo'], header=False, index=False, startrow=len(df_report_finally)+8, startcol=len(lst_group_by) - 1)
            worksheet = writer.sheets['Auxiliar']
            # Agregar formatos al excel
            cell_format_title = writer.book.add_format({'bold': True, 'align': 'center'})
            cell_format_title.set_font_name('Calibri')
            cell_format_title.set_font_size(15)
            cell_format_title.set_font_color('#1F497D')
            cell_format_text_generate = writer.book.add_format({'text_wrap': True,'bold': False, 'align': 'left'})
            cell_format_text_generate.set_font_name('Calibri')
            cell_format_text_generate.set_font_size(10)
            cell_format_text_generate.set_font_color('#1F497D')
            #Encabezado
            cant_columns = (len(lst_group_by) - 1) + 4
            text_generate = 'Generado por: \n %s \nFecha: \n %s %s \nTipo de auxiliar: \n %s' % (
                                self.env.user.name, datetime.now(timezone(self.env.user.tz)).date(),
                                datetime.now(timezone(self.env.user.tz)).time(), type_auxiliary_txt)
            worksheet.merge_range(0, 0, 0, cant_columns - 2, self.company_id.name, cell_format_title)
            worksheet.merge_range(1, 0, 1, cant_columns - 2, self.company_id.company_registry, cell_format_title)
            worksheet.merge_range(0, cant_columns - 1, 3, cant_columns, text_generate,cell_format_text_generate)
            worksheet.merge_range(2, 0, 2, cant_columns - 2, 'AUXILIAR - ' + period_txt, cell_format_title)
            worksheet.merge_range(3, 0, 3, cant_columns - 2, str(date_start)+' - '+str(date_end),cell_format_title)
            # Dar tamaño a las columnas y formato
            position_initial = 0
            for c in columns:
                size = len(c)
                size_tmp = max(len(str(j)) for j in df_report_original[c])
                size = size if size >= size_tmp else size_tmp
                size = size if size <= 300 else 300
                format_align = writer.book.add_format({'align': 'left'})
                number_format = writer.book.add_format({'num_format': '#,##0.00'})
                if c in ['Saldo Anterior','Débito','Crédito','Nuevo Saldo']:
                    worksheet.set_column(position_initial, position_initial, size + 10,number_format)
                else:
                    worksheet.set_column(position_initial, position_initial, size + 10,format_align)
                position_initial +=1
            # Guardar excel
            writer.save()

            self.write({
                'excel_file': base64.encodebytes(stream.getvalue()),
                'excel_file_name': filename,
            })

            action = {
                'name': filename,
                'type': 'ir.actions.act_url',
                'url': "web/content/?model=account.auxiliary.report.filters&id=" + str(
                    self.id) + "&filename_field=excel_file_name&field=excel_file&download=true&filename=" + self.excel_file_name,
                'target': 'self',
            }
            return action
        # -------------------------------------------Crear HTML------------------------------------------------------
        else:
            columns = lst_group_by + ['Saldo Anterior', 'Débito', 'Crédito', 'Nuevo Saldo']
            sizes = []
            for c in columns:
                size = len(c)
                size_tmp = max(len(str(j)) for j in df_report_original[c])
                size = size if size >= size_tmp else size_tmp
                size = size*15 if size*15 <= 500 else 500
                sizes.append(size)

            columns = lst_group_by + ['Saldo Anterior', 'Débito', 'Crédito', 'Nuevo Saldo']
            period_txt = f'PERIODO {self.date_start} a {self.date_end}'
            type_auxiliary_txt = dict(self._fields['type_auxiliary'].selection).get(self.type_auxiliary)
            text_generate = 'Generado por: %s <br/> Fecha: %s %s <br/> Tipo de auxiliar: %s' % (
                self.env.user.name, datetime.now(timezone(self.env.user.tz)).date(),
                datetime.now(timezone(self.env.user.tz)).time(), type_auxiliary_txt)

            html = '''
                    <div class="d-flex justify-content-center">                        
                        <div class="text-center">
                            <h2>%s</h2>
                            <h2>%s</h2>
                            <h2>%s</h2>
                            <h2>%s</h2>
                        </div>
                    </div>
                    <div class="d-flex justify-content-end">
                        <div class="text-right">
                            <p>%s</p>
                        </div>                        
                    </div>
                    <br/><br/>  
                    <div class="d-flex justify-content-center">                  
            ''' % (self.company_id.name,self.company_id.company_registry,'AUXILIAR - ' + period_txt,
                   str(date_start)+' - '+str(date_end),text_generate)
            html += df_report_finally.to_html(col_space='200px', columns=columns, float_format='{:,.2f}'.format, index=False, justify='left')
            html += '''
                    </div>
                    <br/><br/>
                    <div class="d-flex justify-content-center">
            '''
            html += df_total.to_html(col_space='200px', float_format='{:,.2f}'.format, index=False, justify='left')
            html += '</div>'
            return html
