# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrContributionRegister(models.Model):
    _name = "hr.contribution.register"
    _description = "Contribution Register"

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one("res.partner", string="Partner")
    name = fields.Char(required=True)
    note = fields.Text(string="Description")
    type_reg_contribution = fields.Selection([('eps', 'EPS'), 
                                                ('fond_pens', 'Fondo de Pensiones'),
                                                ('fond_censa', 'Fondo de Cesantías'),
                                                ('arl', 'ARL'),
                                                ('caja', 'Caja de Compensación'),], string='Type Reg Contribution')

