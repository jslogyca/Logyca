# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HRRisk(models.Model):
    _name = 'hr.risk'
    _inherit = ['mail.thread']
    _description = "HR Risk"
    _order = "name desc"

    name = fields.Char('Name', tracking=True)
    code = fields.Char('Code', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, tracking=True)
    percentage = fields.Float('Percentage', tracking=True)
