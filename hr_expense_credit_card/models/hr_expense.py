# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Proveedor',
        tracking=True,
        help='Proveedor que generó el gasto',
    )
    
    payment_mode = fields.Selection(
        selection_add=[('credit_card', 'Tarjeta de Crédito')],
        ondelete={'credit_card': 'set default'}
    )
    
    budget_group_id = fields.Many2one(
        'logyca.budget_group', 
        string='Budget Group', 
        ondelete='restrict'
    )
    
    # Campos para valor excluido de IVA
    amount_tax_excluded = fields.Monetary(
        string='Valor Excluido del IVA',
        currency_field='currency_id',
        default=0.0,
        tracking=True,
        help='Valor que no hace parte de la base del IVA pero se suma al total del gasto. '
             'Por ejemplo: propinas, servicios adicionales no gravados, etc.'
    )
    
    amount_tax_excluded_description = fields.Char(
        string='Descripción Valor Excluido',
        tracking=True,
        help='Descripción del concepto del valor excluido del IVA'
    )
    
    # Campo computado para el total incluyendo valor excluido
    total_amount_with_excluded = fields.Monetary(
        string='Total con Valor Excluido',
        compute='_compute_total_amount_with_excluded',
        currency_field='currency_id',
        store=True,
        help='Total del gasto incluyendo el valor excluido del IVA'
    )

    @api.onchange('budget_group_id')
    def onchange_budget_group(self):
        if self.budget_group_id:
            self.analytic_distribution = self.budget_group_id.analytic_distribution
        else:
            self.analytic_distribution = False
    
    @api.depends('total_amount', 'amount_tax_excluded')
    def _compute_total_amount_with_excluded(self):
        """
        Calcula el total incluyendo el valor excluido del IVA
        """
        for expense in self:
            expense.total_amount_with_excluded = expense.total_amount + expense.amount_tax_excluded    
