# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class CrmTeam(models.Model):
    _inherit = 'crm.team'

    free_member = fields.Boolean(string='Periodo de Prueba', default=False)    
