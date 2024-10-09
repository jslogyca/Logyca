# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    prenomina = fields.Boolean('Prenomina')
    sequence_report = fields.Integer('Report Sequence')
