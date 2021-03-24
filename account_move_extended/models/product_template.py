# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    inter_company = fields.Boolean('Intercompany', default=False)