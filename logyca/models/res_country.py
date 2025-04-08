# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResCountry(models.Model):
    _inherit = 'res.country'
	
    x_code_dian = fields.Char(string='Código del país para la DIAN')