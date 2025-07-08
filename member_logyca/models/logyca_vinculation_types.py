# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VinculationTypes(models.Model):
    _inherit = 'logyca.vinculation_types'

    membertyb = fields.Boolean(string='Membresía Periodo de Prueba', default=False)
