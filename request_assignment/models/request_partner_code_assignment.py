# -*- coding: utf-8 -*-

from odoo import fields, models
from datetime import date, timedelta


class RequestPartnerCodeAssignment(models.Model):
    _name = 'request.partner.code.assignment'
    _description = 'Request Partner Code Assignment'
    _order_by = 'date_requisition desc'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    vat = fields.Char(string='NIT')
    id_requisition = fields.Char(string='ID Requisition')
    type_requisition = fields.Many2one('request.partner.assignment.type', string='Request Type')
    user_requisition = fields.Char(string='User Requisition')
    date_requisition = fields.Datetime(string='Date Requisition', default=fields.Datetime.now)
    user_approved = fields.Char(string='User Requisition Approved')
    date_approved = fields.Datetime(string='Date Requisition Approved')
    comments_requisition = fields.Text(string='Comments Requisition')
    file_requisition = fields.Many2one('ir.attachment',string='Attachment')
    state_requisition = fields.Char(string="State Requisition", help='Status of the requisition',)

    def name_get(self):
        return [(request.id, '%s - %s' %
                 (request.partner_id.name, request.type_requisition.name)) for request in self]
