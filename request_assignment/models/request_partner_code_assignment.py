# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import date, timedelta


class RequestPartnerCodeAssignment(models.Model):
    _name = 'request.partner.code.assignment'
    _description = 'Request Partner Code Assignment'
    
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    vat = fields.Char(string='NIT')
    id_requisition = fields.Char(string='ID Requisition')
    type_requisition = fields.Many2one('request.partner.assignment.type', string='Request Type')
    user_requisition = fields.Char(string='User Requisition')
    date_requisition = fields.Date(string='Date Requisition', default=fields.Date.context_today)
    user_approved = fields.Char(string='User Requisition Approved')
    date_approved = fields.Date(string='Date Requisition Approved', default=fields.Date.context_today)
    comments_requisition = fields.Text(string='Comments Requisition')
    file_requisition = fields.Many2one('ir.attachment',string='Attachment')
    # user_attachments = fields.One2many('request.assignment.attachment', 'request_assignment_id', string="assignment attach", index=True)
    response_attachments = fields.Text(string='Response Attachments')

    def name_get(self):
        return [(request.id, '%s - %s' %
                 (request.partner_id.name, request.type_requisition.name)) for request in self]

