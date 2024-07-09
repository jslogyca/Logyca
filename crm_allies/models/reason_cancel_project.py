# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ReasonCancelProject(models.Model):
    _name = 'reason.cancel.project'
    _description = 'Reason Cancel Project'

    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean('Active', default=True)

    def name_get(self):
        return [(reason.id, '%s - %s' %
                 (reason.name, reason.code)) for reason in self]
