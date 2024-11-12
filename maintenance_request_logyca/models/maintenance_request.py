# -*- coding: utf-8 -*-

from odoo import fields, models


class MaintenanceRequest(models.Model):
    _inherit = "maintenance.request"

    equipment_ids = fields.One2many('maintenance.equipment', 'request_id', string="maintenance", index=True)
    equipment_asset_ids = fields.Many2many(string="Maintenance", comodel_name='maintenance.equipment', ondelete='restrict', 
                                                context={'active_test': False}, tracking=True)
