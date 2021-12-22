# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError

class PartnerLogycaRevenue(models.Model):
    _name= 'partner.logyca.revenue'
    _description = "Partner Logyca Revenue"

    config_discount_id = fields.Many2one('config.discount.log.revenue', string='Discount', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    year = fields.Integer(string='Año', required=True)

    def name_get(self):
        return [(logycaedx.id, '%s - %s' % (logycaedx.config_discount_id.name, logycaedx.partner_id.name)) for logycaedx in self]

    @api.model
    def create(self, values):
        if values.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id', '=', values.get('partner_id', False))])
            if partner_id:
                partner_id.write({'revenue_discount_id': values.get('config_discount_id', False)})
        return super(PartnerLogycaRevenue, self).create(values)        

    def write(self, values):
        if values.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id', '=', values.get('partner_id', False))])
            if partner_id:
                partner_id.write({'revenue_discount_id': self.config_discount_id.id})
        return super(PartnerLogycaRevenue, self).write(values)