# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class CrmTeamMember(models.Model):
    _inherit = 'crm.team.member'

    free_member_one = fields.Boolean(string='Periodo de Prueba 1', default=False)
    free_member_two = fields.Boolean(string='Periodo de Prueba 2', default=False)
    free_member_shop = fields.Boolean(string='Periodo de Prueba Shop', default=False)
