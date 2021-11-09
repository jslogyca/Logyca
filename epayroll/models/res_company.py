# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit= 'res.company'

    connection_payslip_id = fields.Many2one('connection.server', string='Connection Epayslip')
