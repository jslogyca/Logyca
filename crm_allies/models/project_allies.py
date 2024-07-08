# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProjectAllies(models.Model):
    _name = 'project.allies'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ProjectAllies'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Partner")
    year_id = fields.Many2one('account.fiscal.year', string="Year")
    object = fields.Char('Object')
    indicator = fields.Char('Indicator')
    project_present = fields.Char('Present Project')
    project_last = fields.Char('Last Project')
    advance_last = fields.Char('Last Advance')
    advance_ids = fields.One2many('project.allies.line', 'project_id', string="Advances", index=True)


class ProjectAlliesLine(models.Model):
    _name = 'project.allies.line'

    name = fields.Char('Name')
    advance = fields.Char('Advance')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Partner")
    project_id = fields.Many2one('project.allies', string="Project")

