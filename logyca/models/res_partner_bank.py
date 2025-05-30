# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'
    
    x_studio_tipo_de_cuenta = fields.Selection([('Corriente', 'Corriente'),
                              ('Ahorros', 'Ahorros')], string='Tipo de cuenta')
