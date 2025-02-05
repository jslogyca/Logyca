# -*- coding: utf-8 -*-

from odoo import fields, models


class RequestAssignmentAttachMent(models.Model):
    _name = 'request.assignment.attachment'
    _description = 'Request Assignment AttachMent'

    name = fields.Char(string='Name')
    path = fields.Char(string='Path')
    request_assignment_id = fields.Many2one(
        'request.partner.code.assignment',
        string='Request Assignment'
    )

    def action_download_file(self):
        """ This function returns an action that display a download button to the user"""
        return {
            'type': 'ir.actions.act_url',
            'url': self.path,
            'target': 'new',
        }
