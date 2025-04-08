# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCountryState(models.Model):
    _inherit = 'res.country.state'
	
    x_code_dian = fields.Char(string='Código de provincia/departamento para la DIAN')
