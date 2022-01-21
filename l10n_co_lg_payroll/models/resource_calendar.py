# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    days_per_month = fields.Float('Days Per Month', default=0.0)
