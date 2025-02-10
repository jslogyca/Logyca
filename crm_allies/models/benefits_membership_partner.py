# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class BenefitsMembershipPartner(models.Model):
    _name = 'benefits.membership.partner'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Benefits Membership Partner'

    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    vat = fields.Char(string='NIF')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    benefit_id = fields.Many2one('benefits.membership', string="Benefits Membership", required=True)
    categ_id = fields.Many2one('categ.benefits.membership', string="Categ", required=True)
    information = fields.Text(string='Information')
    cant_assistants = fields.Integer(string='Cant Assistants')
    cant_company = fields.Integer(string='Cant Company')
    origin = fields.Char(string='Origin')
    company_user_id = fields.Many2one('res.partner', string='User Company')
    company_user = fields.Char('User Company')
    company_email = fields.Char(string='Email Company')
    partner_user_id = fields.Many2one('res.partner', string='User Partner')
    date_done = fields.Date(string='Done Date', default=fields.Date.context_today)
    sector_id = fields.Many2one('logyca.sectors', string='Sectors', related='partner_id.x_sector_id')

    def name_get(self):
        return [(benefit.id, '%s - %s' %
                 (benefit.partner_id.name, benefit.benefit_id.name)) for benefit in self]
