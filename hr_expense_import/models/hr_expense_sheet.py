# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_submit_sheet(self):
        """Acción para enviar a aprobar el reporte de gastos"""
        self.write({'approval_state': 'submit'})
        return True

    def action_submit_sheets_batch(self):
        """Acción para enviar a aprobar múltiples reportes de gastos"""
        for sheet in self:
            if sheet.state == 'draft':
                sheet.action_submit_sheet()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Reportes Enviados'),
                'message': _('%s reporte(s) de gastos enviado(s) a aprobación.') % len(self),
                'type': 'success',
                'sticky': False,
            }
        }
