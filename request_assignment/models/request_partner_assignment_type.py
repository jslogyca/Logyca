# -*- coding: utf-8 -*-

from odoo import fields, models


class RequestPartnerAssignmentType(models.Model):
    _name = 'request.partner.assignment.type'
    _description = 'Request Partner Assignment Type'
    
    code = fields.Char(string='Code')
    name = fields.Char(string='Name')
    active = fields.Boolean(string='Active', default=True)    

    def name_get(self):
        return [(request.id, '%s - %s' %
                 (request.code, request.name)) for request in self]
