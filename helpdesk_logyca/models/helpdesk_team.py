# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    ticket_interno = fields.Boolean('Interno', default=False)

