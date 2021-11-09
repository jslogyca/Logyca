# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class HREpayslipsNotewizard(models.TransientModel):
    _name = 'hr.epayslips.note.wizard'
    _description = 'Generate epayslips note '

    type_note_id = fields.Many2one('type.note.epayroll', string='Tipo de Nota de Ajuste')

    def compute_sheet_epayslip_note(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            epayslip_id = self.env['epayslip.bach'].search([('id','=',active_id)])
        type_document = self.env['type.epayroll'].search([('document_type','=','payslip_ajuste')], limit=1)
        if not type_document:
            raise ValidationError('No existe tipo de Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica!')
        from_date = epayslip_id.start_date
        to_date = epayslip_id.finish_date
        name = 'Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica'
        for employee in epayslip_id.employee_id:
            contract_id = self.env['hr.contract'].search([('employee_id','=',employee.id)], limit=1)
            if not contract_id:
                raise ValidationError('No existe un contrato!')
            res = {
                'employee_id': employee.id,
                'contract_id': contract_id.id,
                'name': name,
                'epayslip_bach_run_id': epayslip_id.epayslip_bach_run_id.id,
                'start_date': from_date,
                'finish_date': to_date,
                'company_id': employee.company_id.id,
                'type_epayroll': type_document.id,
                'epayslip_origin': epayslip_id.id,
                'type_note_paysip': self.type_note_id.id,
            }
            epayslips = self.env['epayslip.bach'].create(res)
            self._cr.commit()
        epayslip_id.write({'state': 'cancel_nota'})
        return {'type': 'ir.actions.act_window_close'}
