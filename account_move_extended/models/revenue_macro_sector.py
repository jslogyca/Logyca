# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _


class RevenueMacroSector(models.Model):
    _name = "revenue.macro.sector"
    _description = "Income Macro Sector"
    _order = "id desc"


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    amount = fields.Char('Ingresos')

    def name_get(self):
        return [(type.id, '%s' % (type.amount)) for type in self]



class RevenueMacroSectorPartner(models.Model):
    _name = "revenue.macro.sector.partner"
    _description = "Income Macro Sector Partner"
    _order = "id desc"

    
    revenue_ids = fields.Many2one('revenue.macro.sector', string='Ingresos Partner')
    partner_id = fields.Many2one('res.partner', string='Partner')
    macro_sector = fields.Selection(related='partner_id.macro_sector', string='Macrosector')