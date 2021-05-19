# -*- coding: utf-8 -*-

from odoo import models
import json

class ReportCertificationReport(models.AbstractModel):
    _inherit = 'l10n_co_reports.certification_report'

    def print_pdf(self, options):
        lines = self._get_lines(options)
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'l10n_co_reports.retention_report.wizard',
            'views': [(self.env.ref('l10n_co_reports.retention_report_wizard_form').id, 'form')],
            'view_id': self.env.ref('l10n_co_reports.retention_report_wizard_form').id,
            'target': 'new',
            'context': {'lines': lines, 'report_name': self._name, 'date_from' : options['date'].get('date_from'), 'date_to' : options['date'].get('date_to')},
            'data': {'options': json.dumps(options), 'output_format': 'pdf'},
        }
