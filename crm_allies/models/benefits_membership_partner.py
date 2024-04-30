# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class BenefitsMembershipPartner(models.Model):
    _name = 'benefits.membership.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Benefits Membership Partner'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    benefit_id = fields.Many2one('benefits.membership', string="Benefits Membership", required=True)
    categ_id = fields.Many2one('categ.benefits.membership', string="Categ", required=True)
    information = fields.Text(string='Information')
    cant_assistants = fields.Integer(string='Cant Assistants')
    cant_company = fields.Integer(string='Cant Company')
    origin = fields.Char(string='Origin')
    company_user_id = fields.Many2one('res.partner', string='User Company')
    company_email = fields.Char(string='Email Company')
    partner_user_id = fields.Many2one('res.partner', string='User Partner')
    date_done = fields.Date(string='Done Date', default=fields.Date.context_today)
