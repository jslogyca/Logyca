# -*- coding: utf-8 -*-
from odoo import fields, models

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    x_vac_carry_prev_year = fields.Float(
        string="Vacaciones Acumuladas Año Anterior (manual)",
        help="Si se informa, este valor sobrescribe el cálculo automático para 'VAC ACUMULADAS DIC {año-1}'."
    )
