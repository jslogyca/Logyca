# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import date, timedelta


class RequestPartnerCodeAssignment(models.Model):
    _inherit = 'request.partner.code.assignment'

    response_attachments = fields.Text(string='Response Attachments')
    prefixes_sent = fields.Text(string='Prefixes Sent')
    prefixes_approved = fields.Text(string='Prefixes Approved')
    total_transfer = fields.Boolean('Total Transfer', default=False)
    partner_receiver_id = fields.Many2one('res.partner', string='Partner Receiver')
    user_attachments = fields.One2many(
        'request.assignment.attachment',
        'request_assignment_id',
        string="assignment attach",
        index=True
    )
