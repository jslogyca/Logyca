# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRPayslipRun(models.Model):
    _inherit = "hr.payslip.run"

    def do_draft(self):
        for run in self:
            run.write({'state': 'draft'})
