# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    income_ids = fields.One2many('revenue.macro.sector.partner', 'partner_id', string='Ingresos')
    

