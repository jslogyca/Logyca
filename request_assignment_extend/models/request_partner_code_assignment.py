# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import date, timedelta


class RequestPartnerCodeAssignment(models.Model):
    _inherit = 'request.partner.code.assignment'
    
    user_attachments = fields.One2many('request.assignment.attachment', 'request_assignment_id', string="assignment attach", index=True)
    response_attachments = fields.Text(string='Response Attachments')
