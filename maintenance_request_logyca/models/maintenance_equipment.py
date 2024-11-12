# -*- coding: utf-8 -*-

from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = "maintenance.equipment"

    request_id = fields.Many2one('maintenance.request', string="Maintenance")
