# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    x_discount_account = fields.Boolean(string='Cuenta asignada para descuento')   
