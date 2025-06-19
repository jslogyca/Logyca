# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class CRMTeam(models.Model):
    _inherit = 'crm.team'

    total_amount = fields.Float(string='Meta de Facturación', default=0.00)
    total_goal = fields.Boolean(compute='_compute_last_date', string='Total Goal')
        
    @api.depends('crm_team_member_ids', 'crm_team_member_ids.crm_team_id', 'crm_team_member_ids.total_amount', 'crm_team_member_ids.date_start')
    def _compute_last_date(self):
        for record in self:
            # Encuentra el total            
            record.total_amount = sum(record.crm_team_member_ids.mapped('total_amount'))
            record.total_goal = True
