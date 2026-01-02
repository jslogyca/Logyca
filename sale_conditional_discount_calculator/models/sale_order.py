# -*- coding: utf-8 -*-

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Campos para primer descuento condicionado
    x_conditional_discount = fields.Monetary(
        string='Descuento Condicionado 1',
        currency_field='currency_id',
        help='Valor del descuento condicionado calculado para la primera fecha'
    )
    
    x_conditional_discount_deadline = fields.Date(
        string='Fecha Límite Descuento 1',
        help='Fecha límite para aplicar el primer descuento condicionado'
    )
    
    x_amount_total_conditional_discount = fields.Monetary(
        string='Total con Descuento 1',
        currency_field='currency_id',
        compute='_compute_amount_total_conditional_discount',
        store=True,
        help='Total de la orden menos el descuento condicionado 1'
    )
    
    # Campos para segundo descuento condicionado
    x_conditional_discount_second_date = fields.Monetary(
        string='Descuento Condicionado 2',
        currency_field='currency_id',
        help='Valor del descuento condicionado calculado para la segunda fecha'
    )
    
    x_conditional_discount_deadline_second_date = fields.Date(
        string='Fecha Límite Descuento 2',
        help='Fecha límite para aplicar el segundo descuento condicionado'
    )
    
    x_amount_total_conditional_discount_second_date = fields.Monetary(
        string='Total con Descuento 2',
        currency_field='currency_id',
        compute='_compute_amount_total_conditional_discount_second_date',
        store=True,
        help='Total de la orden menos el descuento condicionado 2'
    )
    
    @api.depends('amount_total', 'x_conditional_discount')
    def _compute_amount_total_conditional_discount(self):
        """Calcula el total con el primer descuento condicionado"""
        for order in self:
            order.x_amount_total_conditional_discount = order.amount_total - order.x_conditional_discount
    
    @api.depends('amount_total', 'x_conditional_discount_second_date')
    def _compute_amount_total_conditional_discount_second_date(self):
        """Calcula el total con el segundo descuento condicionado"""
        for order in self:
            order.x_amount_total_conditional_discount_second_date = order.amount_total - order.x_conditional_discount_second_date
