# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class EPayslipLine(models.Model):
    _name = 'epayslip.line'
    _description = 'EPayslip Line'
    _rec_name = 'name'

    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary rule')
    electronictag_id = fields.Many2one('hr.electronictag.structure', string='Electronic Tags')
    value = fields.Float(string="Valor", default=0.00) # Agregar tipo de moneda 
    epayslip_bach_id = fields.Many2one('epayslip.bach', string='Epayslip bach', ondelete="cascade") 
    employee_id = fields.Many2one('hr.employee', string='HR employee')
    bach_run_id = fields.Many2one('epayslip.bach.run', string='Bach Run')
    name = fields.Char(string='name')

#