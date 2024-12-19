# -*- coding: utf-8 -*-

from odoo import fields, models


class RequestAssignmentAttach(models.Model):
    _name = 'request.assignment.attach'
    _description = 'Request Assignment Attach'
    
    name = fields.Char(string='Name')
    path = fields.Char(string='Path')
    request_assignment_id = fields.Many2one('request.partner.code.assignment', string='Request Assignment')
