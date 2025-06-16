# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EPayslipBachRun(models.Model):
    _name = 'epayslip.bach.run'
    _description = 'EPayslip Bach Run'
    _inherit = ['mail.thread']


    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    start_date = fields.Date(string='Start date')
    finish_date = fields.Date(string='Finish date')
    epayslip_bach_ids = fields.One2many('epayslip.bach', 'epayslip_bach_run_id', string='Epayslip bach')
    state = fields.Selection([('draft', 'Draft'), 
                                ('generated', 'Generated'),
                                ('sent', 'Sent'),
                                ('cancel', 'Cancel'),
                                ('done', 'Done')], default='draft', string='States') 
    type_epayroll = fields.Many2one('type.epayroll', string='Tipo de XML utilizado')

    def action_draft(self): 
        return self.write({'state': 'draft'})

    def action_cancel(self):
        if self.epayslip_bach_ids:
            for epayslip_bach_id in self.epayslip_bach_ids:
                epayslip_bach_id.unlink()
        return self.write({'state': 'cancel'})

    def action_validate_generate_epayslip(self):
        view_id = self.env.ref('epayroll.hr_epayslips_by_employees_form').id,
        return {
            'name':_("¿Generar EPayslip?"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'hr.epayslips.by.employees',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }

    def update_data(self):
        if self.epayslip_bach_ids:
            for epayslip_bach_id in self.epayslip_bach_ids:
                if epayslip_bach_id.state == 'draft':
                    epayslip_bach_id.update_data()
                    self.env.cr.commit()
            return self.write({'state': 'generated'})
        else:
            raise ValidationError('No existen Nóminas')

    def action_sent(self): 
        if self.epayslip_bach_ids:
            for epayslip_bach_id in self.epayslip_bach_ids:
                if epayslip_bach_id.state == 'generated':
                    epayslip_bach_id.action_sent()
                self._cr.commit()
        return self.write({'state': 'sent'})

    def get_status_validation(self): 
        if self.epayslip_bach_ids:
            for epayslip_bach_id in self.epayslip_bach_ids:
                if epayslip_bach_id.state == 'sent':
                    epayslip_bach_id.get_status_validation()
                self._cr.commit()
        return self.write({'state': 'done'})

    def action_hr_epayslip_file(self):
        view_id = self.env.ref('epayroll_process.hr_epayslip_file_wizard_view').id,
        return {
            'name':_("¿Are you sure ?"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'hr.epayslip.file.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }