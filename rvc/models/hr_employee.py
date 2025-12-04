from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_is_crecemype_consultant = fields.Boolean(string="¿Es consultor?", default=False)
