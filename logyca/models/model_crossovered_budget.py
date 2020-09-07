# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

#---------------------------Modelo CRM_LEAD / OPORTUNIDADES-------------------------------#

class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'
    #Grupo Presupuestal
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal')
    
    def _compute_practical_amount(self):
        for line in self:
            acc_ids = line.general_budget_id.account_ids.ids
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id:
                analytic_line_obj = self.env['account.analytic.line']
                domain = [('account_id', '=', line.analytic_account_id.id),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ]
                if acc_ids:
                    domain += [('general_account_id', 'in', acc_ids)]
                #Logica grupo presupuestal 
                if line.x_budget_group.id:
                    domain += [('move_id.x_budget_group', '=', line.x_budget_group.id)]
                
                where_query = analytic_line_obj._where_calc(domain)
                analytic_line_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

            else:
                aml_obj = self.env['account.move.line']
                domain = [('account_id', 'in',
                           line.general_budget_id.account_ids.ids),
                          ('date', '>=', date_from),
                          ('date', '<=', date_to),
                          ('move_id.state', '=', 'posted')
                          ]
                #Logica grupo presupuestal 
                if line.x_budget_group.id:
                    domain += [('x_budget_group', '=', line.x_budget_group.id)]
                
                where_query = aml_obj._where_calc(domain)
                aml_obj._apply_ir_rules(where_query, 'read')
                from_clause, where_clause, where_clause_params = where_query.get_sql()
                select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause
                
            self.env.cr.execute(select, where_clause_params)
            line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    
    
