# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = 'res.users'


    group_manager = fields.Boolean('Cargo Grupo Directivo', default=False)