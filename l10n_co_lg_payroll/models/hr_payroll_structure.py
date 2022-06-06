# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRPayrollStructure(models.Model):
    _inherit = "hr.payroll.structure"

    payroll_liquid = fields.Boolean('Liquid', default=False)
