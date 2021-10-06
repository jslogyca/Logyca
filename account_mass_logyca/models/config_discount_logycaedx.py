# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError

class ConfigDiscountLogycaEDX(models.Model):
    _name= 'config.discount.logycaedx'
    _inherit = ['mail.thread']
    _description = "Config Discount Logyca EDX"
    _order = "name desc"


    name = fields.Char('File Name')
    asset_range_id = fields.Many2one('logyca.asset_range', string='Asset Range', tracking=True)
    company_size = fields.Selection([
                        ('micro', 'Micro'),
                        ('pequenas', 'Pequeñas'),
                        ('medianas', 'Medianas'),
                        ('grandes', 'Grandes')], string='Company Size', tracking=True)
    amount_user = fields.Integer(string='Amount User')
    discount = fields.Float(string='Discount')

    def name_get(self):
        return [(discount.id, '%s - %s' % (discount.asset_range_id.name, discount.discount)) for discount in self]

    @api.model
    def create(self, values):
        if values.get('asset_range_id', False) and values.get('discount', False):
            asset_range_id = self.env['logyca.asset_range'].search([('id', '=', values.get('asset_range_id', False))])
            if asset_range_id:
                values['name'] = asset_range_id.name + str(values.get('discount', False))
        return super(ConfigDiscountLogycaEDX, self).create(values)        

    def write(self, values):
        if values.get('asset_range_id', False) and values.get('discount', False):
            asset_range_id = self.env['logyca.asset_range'].search([('id', '=', values.get('asset_range_id', False))])
            if asset_range_id:
                values['name'] = asset_range_id.name + str(values.get('discount', False))
        return super(ConfigDiscountLogycaEDX, self).write(values)        
