# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

import base64


class ProjectAlliesCancelWizard(models.TransientModel):
    _name = 'project.allies.cancel.wizard'

    advance = fields.Char('Advance')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    reason_id = fields.Many2one('reason.cancel.project', string='Reason')

    def save_detail_advance(self):
        self.ensure_one()
        project_id = self.env['project.allies'].browse(self._context.get('active_id'))
        project_line_id = self.env['project.allies.line']
        project_line_id.create({
            'advance': self.advance,
            'company_id': self.company_id.id,
            'project_id': project_id.id,
            'date': self.date,
        })

    def cancel_project(self):
        self.ensure_one()
        project_id = self.env['project.allies'].browse(self._context.get('active_id'))
        date = fields.Date.context_today
        for project_id in self:
            project_id.write({'state': 'cancel', 'date_cancel': date, 'reason_id': self.reason_id.id})

    def save_detail_advance_new(self):
        self.ensure_one()
        self.save_detail_advance()
        project_wizard_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        context = {}
        context.update(active_model=self._context.get('active_model'),
                       active_id=project_wizard_id.id)
        return {
            'name': 'Cancel Project',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_allies.project_allies_cancel_wizard_view_form').id,
            'res_model': 'project.allies.cancel.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context
            }
