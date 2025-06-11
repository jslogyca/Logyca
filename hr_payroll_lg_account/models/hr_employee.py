# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    
    partner_eps = fields.Many2one('res.partner', string='EPS', domain="[('type_reg_contribution', '=', 'eps')]")
    partner_fond_pens = fields.Many2one('res.partner', string='Fondo de Pensiones', domain="[('type_reg_contribution', '=', 'fond_pens')]")
    partner_accai_pens = fields.Many2one('res.partner', string='ACCAI', domain="[('type_reg_contribution', '=', 'accai')]")
    partner_fond_censa = fields.Many2one('res.partner', string='Fondo de Cesantías', domain="[('type_reg_contribution', 'in', ('fond_censa', 'fond_pens'))]")
    partner_arl = fields.Many2one('res.partner', string='ARL', domain="[('type_reg_contribution', '=', 'arl')]")
    partner_caja = fields.Many2one('res.partner', string='Caja de Compensación', domain="[('type_reg_contribution', '=', 'caja')]")

    @api.depends('work_contact_id', 'work_contact_id.mobile', 'work_contact_id.email', 'work_contact_id.vat','work_contact_id.name')
    def _compute_work_contact_details(self):
        # Llama al compute original para mantener la lógica existente
        super(HREmployee, self)._compute_work_contact_details()
        # Añade tu asignación extra
        for employee in self:
            if employee.work_contact_id:
                # Rellena identification_id con el VAT del contacto
                employee.identification_id = employee.work_contact_id.vat or False
                employee.name = employee.work_contact_id.name or False
                employee.private_street = employee.work_contact_id.street or False
                employee.private_email = employee.work_contact_id.email
