# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ConnectionServer(models.Model):
    _name = 'connection.server'
    _description = 'Connection Server'
    _inherit = ['mail.thread']


    name = fields.Char('Name Connection', required=True)
    type = fields.Selection([
        ('2', 'Test'),
        ('1', 'Production')
    ], required=True, string='Type', default='1')
    software_code = fields.Char('Software Identification Code', required=True)
    pin_software = fields.Char('Software PIN', required=True)
    software_password = fields.Char('Software Password')
    test_set_id = fields.Char(string='ID set de pruebas', required=True)
    connection_url = fields.Char('Connection URL', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string="Status", required=True, tracking=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    certificate_id = fields.Many2one('ecertificate', string='Certificate', required=True)
    sequence_id = fields.Many2one('ir.sequence', string='Secuencia nombre XML')

    def active_connect_server(self):
        return self.write({'state': 'active'})

    def inactive_connect_server(self):
        return self.write({'state': 'inactive'})

    def draft_connect_server(self):
        return self.write({'state': 'draft'})
