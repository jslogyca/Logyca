# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProjectAllies(models.Model):
    _name = 'project.allies'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ProjectAllies'

    @api.depends('vinculation', 'x_type_vinculation', 'company_id', 'partner_id')
    def _get_vinculation(self):
        for help in self:
            if help.partner_id:
                if help.partner_id.x_type_vinculation:
                    miembro = False
                    for vinculation_id in help.partner_id.x_type_vinculation:
                        if miembro:
                            continue
                        help.x_type_vinculation = vinculation_id.id
                        if vinculation_id.id == 1:
                            miembro = True
                    help.vinculation = True
                else:
                    help.x_type_vinculation = 12
                    help.vinculation = True
            else:
                help.vinculation = True

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Partner", domain="[('allies_logyca', '=', True)]")
    year_id = fields.Many2one('account.fiscal.year', string="Year")
    object = fields.Char('Object')
    indicator = fields.Char('Indicator')
    project_present = fields.Char('Present Project')
    project_last = fields.Char('Last Project')
    advance_last = fields.Char('Last Advance')
    advance_ids = fields.One2many('project.allies.line', 'project_id', string="Advances", index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today)
    type_allies = fields.Selection(related='partner_id.type_allies', store=True)
    sub_type_allies = fields.Selection(related='partner_id.sub_type_allies', store=True)
    allies_user_id = fields.Many2one(related='partner_id.allies_user_id', store=True)
    state = fields.Selection([('draft', 'Draft'),
                                ('open', 'Open'),
                                ('cancel', 'Cancel'),
                                ('done', 'Done'),
        ], string='Status', default='draft')
    apply_amount = fields.Boolean('Apply Amount', default=False)
    total_amount = fields.Float(string='Total Amount', default=0.00)
    date_cancel = fields.Date(string='Date', default=fields.Date.context_today)
    date_open = fields.Date(string='Date', default=fields.Date.context_today)
    date_done = fields.Date(string='Date', default=fields.Date.context_today)
    reason_id = fields.Many2one('reason.cancel.project', string='Reason')
    x_type_vinculation = fields.Many2one('logyca.vinculation_types', string='Tipo de vinculación')
    vinculation = fields.Boolean(compute='_get_vinculation', string='Vinculation')    

    def name_get(self):
        return [(project.id, '%s - %s' %
                 (project.partner_id.name, project.project_present)) for project in self]

    def save_detail_advance(self):
        return {
            'name': 'Add Avances del Proyecto',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_allies.project_allies_wizard_view_form').id,
            'res_model': 'project.allies.cancel.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self._context
        }

    def cancel_project(self):
        return {
            'name': 'Cancel Project',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('crm_allies.project_allies_cancel_wizard_view_form').id,
            'res_model': 'project.allies.cancel.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self._context
        }

    def open_project(self):
        date = fields.Datetime.now()
        for project in self:
            project.write({'state': 'open', 'date_open': date})

    def done_project(self):
        date = fields.Datetime.now()
        for project in self:
            project.write({'state': 'done', 'date_done': date})

    def draft_project(self):
        date = fields.Datetime.now()
        for project in self:
            project.write({'state': 'draft'})


class ProjectAlliesLine(models.Model):
    _name = 'project.allies.line'
    _description = 'Project Allies Line'

    name = fields.Char('Name')
    advance = fields.Char('Advance')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    project_id = fields.Many2one('project.allies', string="Project")
    date = fields.Date(string='Date', default=fields.Date.context_today)
    state_activity = fields.Selection([('in_progress', 'In Progress'),
                                ('end', 'End'),
        ], string='Status Activity', default='in_progress')    

    def name_get(self):
        return [(project.id, '%s - %s' %
                 (project.project_id.partner_id.name, project.project_id.project_present)) for project in self]
