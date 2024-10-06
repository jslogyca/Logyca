# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _


class RevenueMacroSector(models.Model):
    _name = "revenue.macro.sector"
    _description = "Income Macro Sector"
    _order = "amount_start asc"


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    amount = fields.Char('Ingresos')
    amount_start = fields.Float('Ingresos Iniciales')
    amount_end = fields.Float('Ingresos Finales')
    size_sector_int = fields.Selection([('micro1', 'Micro 1'),
                                        ('micro2', 'Micro 2'),
                                        ('micro3', 'Micro 3'), 
                                        ('pequena1', 'Pequeña 1'),
                                        ('pequena2', 'Pequeña 2'),
                                        ('pequena3', 'Pequeña 3'),
                                        ('mediana1', 'Mediana 1'),
                                        ('mediana2', 'Mediana 2'),
                                        ('mediana3', 'Mediana 3'),
                                        ('grande1', 'Grande 1'),
                                        ('grande2', 'Grande 2'),
                                        ('grande3', 'Grande 3'),
                                        ('grande4', 'Grande 4'),
                                    ('grande5', 'Grande 5')], string='Tamaño Internor Empresa Sector')
    x_company_size = fields.Selection([
                                        ('1', 'Microempresa'),
                                        ('2', 'Pequeña'),
                                        ('3', 'Mediana'),
                                        ('4', 'Grande')
                                    ], string='Tamaño empresa', tracking=True)

    def name_get(self):
        return [(type.id, '%s' % (type.amount)) for type in self]



class RevenueMacroSectorPartner(models.Model):
    _name = "revenue.macro.sector.partner"
    _description = "Income Macro Sector Partner"
    _order = "id desc"

    
    revenue_ids = fields.Many2one('revenue.macro.sector', string='Ingresos Partner')
    partner_id = fields.Many2one('res.partner', string='Partner')
    fiscal_id = fields.Many2one('account.fiscal.year', string='Ejercicio fiscal')
    macro_sector = fields.Selection(related='partner_id.macro_sector', string='Macrosector')
    amount = fields.Char('Ingresos')