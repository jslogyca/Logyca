# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CreditCard(models.Model):
    _name = 'credit.card'
    _description = 'Tarjeta de Crédito Corporativa'
    _order = 'name'

    name = fields.Char(
        string='Nombre de la Tarjeta',
        required=True,
        help='Nombre o identificador de la tarjeta de crédito'
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía a la que pertenece esta tarjeta de crédito'
    )    
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Cuenta Contable',
        required=True,
        domain="[('account_type', 'in', ['liability_payable', 'liability_current'])]",
        help='Cuenta contable de CXP para la tarjeta de crédito'
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Tercero/Proveedor',
        required=True,
        help='Proveedor o tercero asociado a la tarjeta de crédito (banco emisor)'
    )
    
    active = fields.Boolean(
        default=True,
        help='Desmarcar para archivar la tarjeta sin eliminarla'
    )
    
    # Campos informativos opcionales
    card_number = fields.Char(
        string='Últimos 4 dígitos',
        size=4,
        help='Últimos 4 dígitos de la tarjeta para identificación'
    )
    
    card_type = fields.Selection(
        selection=[
            ('visa', 'Visa'),
            ('mastercard', 'Mastercard'),
            ('amex', 'American Express'),
            ('diners', 'Diners Club'),
            ('other', 'Otra')
        ],
        string='Tipo de Tarjeta',
        help='Tipo de tarjeta de crédito'
    )
    
    credit_limit = fields.Monetary(
        string='Cupo',
        currency_field='currency_id',
        help='Cupo o límite de crédito de la tarjeta'
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    
    notes = fields.Text(
        string='Notas',
        help='Observaciones adicionales sobre la tarjeta'
    )
    
    _sql_constraints = [
        ('name_company_unique', 'unique(name, company_id)', 
         'Ya existe una tarjeta con este nombre en la compañía!'),
    ]
    
    @api.constrains('card_number')
    def _check_card_number(self):
        """Validar que los últimos 4 dígitos sean numéricos"""
        for record in self:
            if record.card_number and not record.card_number.isdigit():
                raise ValidationError(_('Los últimos 4 dígitos deben ser numéricos.'))
    
    def name_get(self):
        """Personalizar el nombre mostrado en los campos Many2one"""
        result = []
        for record in self:
            name = record.name
            if record.card_number:
                name = f"{name} (****{record.card_number})"
            result.append((record.id, name))
        return result
