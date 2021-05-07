# -*- coding: utf-8 -*-

from odoo import models

class RetentionReportWizard(models.TransientModel):
    _inherit = 'l10n_co_reports.retention_report.wizard'

    def generate_report(self):
        data = {
            'wizard_values': self.read()[0],
            'lines': self._context.get('lines'),
            'report_name': self._context.get('report_name'),
            'date_from': self._context.get('date_from'),
            'date_to': self._context.get('date_to'),
        }