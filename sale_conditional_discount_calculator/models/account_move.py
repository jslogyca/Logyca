# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Campos para primer descuento condicionado
    x_value_discounts = fields.Monetary(
        string='Valor Descuentos 1',
        currency_field='currency_id',
        help='Valor del descuento condicionado calculado para la primera fecha'
    )
    
    x_discounts_deadline = fields.Date(
        string='Fecha Límite Descuentos 1',
        help='Fecha límite para aplicar el primer descuento condicionado'
    )
    
    x_amount_total_discounts = fields.Monetary(
        string='Total con Descuentos 1',
        currency_field='currency_id',
        compute='_compute_amount_total_discounts',
        store=True,
        help='Total de la factura menos el descuento condicionado 1'
    )
    
    # Campos para segundo descuento condicionado
    x_value_discounts_second_date = fields.Monetary(
        string='Valor Descuentos 2',
        currency_field='currency_id',
        help='Valor del descuento condicionado calculado para la segunda fecha'
    )
    
    x_discounts_deadline_second_date = fields.Date(
        string='Fecha Límite Descuentos 2',
        help='Fecha límite para aplicar el segundo descuento condicionado'
    )
    
    x_amount_total_discounts_second_date = fields.Monetary(
        string='Total con Descuentos 2',
        currency_field='currency_id',
        compute='_compute_amount_total_discounts_second_date',
        store=True,
        help='Total de la factura menos el descuento condicionado 2'
    )
    
    @api.depends('amount_total', 'x_value_discounts')
    def _compute_amount_total_discounts(self):
        """Calcula el total con el primer descuento condicionado"""
        for move in self:
            move.x_amount_total_discounts = move.amount_total - move.x_value_discounts
    
    @api.depends('amount_total', 'x_value_discounts_second_date')
    def _compute_amount_total_discounts_second_date(self):
        """Calcula el total con el segundo descuento condicionado"""
        for move in self:
            move.x_amount_total_discounts_second_date = move.amount_total - move.x_value_discounts_second_date
