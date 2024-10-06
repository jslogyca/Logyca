# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError

class ConfigDiscountLogRevenue(models.Model):
    _name= 'config.discount.log.revenue'
    _inherit = ['mail.thread']
    _description = "Config Discount Log Revenue"
    _order = "name desc"


    name = fields.Char('File Name')
    company_size = fields.Selection([
                        ('micro', 'Micro'),
                        ('pequenas', 'Pequeñas'),
                        ('medianas', 'Medianas'),
                        ('grandes', 'Grandes')], string='Company Size', tracking=True)
    amount_user = fields.Integer(string='Amount User')
    discount = fields.Float(string='Discount')
    revenue_range = fields.Many2one('revenue.macro.sector', string='Rango de Ingresos', tracking=True, ondelete='restrict')

    def name_get(self):
        return [(discount.id, '%s - %s' % (discount.revenue_range.amount, discount.discount)) for discount in self]

    @api.model
    def create(self, values):
        if values.get('revenue_range', False) and values.get('discount', False):
            revenue_range_id = self.env['revenue.macro.sector'].search([('id', '=', values.get('revenue_range', False))])
            if revenue_range_id:
                values['name'] = revenue_range_id.amount + str(values.get('discount', False))
        return super(ConfigDiscountLogRevenue, self).create(values)        

    def write(self, values):
        if values.get('revenue_range', False) and values.get('discount', False):
            revenue_range_id = self.env['revenue.macro.sector'].search([('id', '=', values.get('revenue_range', False))])
            if revenue_range_id:
                values['name'] = revenue_range_id.amount + str(values.get('discount', False))                
        return super(ConfigDiscountLogRevenue, self).write(values)        
