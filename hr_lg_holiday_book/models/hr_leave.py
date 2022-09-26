# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

from odoo.exceptions import ValidationError, UserError


class HRLeave(models.Model):
    _inherit = "hr.leave"

    contract_id = fields.Many2one('hr.contract', string='Contract')

    @api.model
    def create(self, vals):
        if vals.get('employee_id', False) or vals.get('holiday_status_id', False):
            contract_id = self.env['hr.contract'].search([('employee_id', '=', vals.get('employee_id', False)), ('state', '=', 'open')], limit=1)
            if contract_id:
                vals['contract_id']= contract_id.id
        res = super(HRLeave, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('employee_id', False) or vals.get('holiday_status_id', False):
            contract_id = self.env['hr.contract'].search([('employee_id', '=', vals.get('employee_id', False)), ('state', '=', 'open')], limit=1)
            if contract_id:
                vals['contract_id']= contract_id.id
        res = super(HRLeave, self).write(vals)
        return res

    @api.onchange('company_id', 'employee_id')
    def _onchange_contract_id(self):
        if self.employee_id and self.id:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')], limit=1)
            if contract_id:
                self.write({'contract_id': contract_id})
            else:
                raise UserError(_("The employee %s is not contract active") % self.employee_id.name)    
