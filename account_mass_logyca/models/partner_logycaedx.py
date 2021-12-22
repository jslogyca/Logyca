# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError, UserError

class PartnerLogycaEDX(models.Model):
    _name= 'partner.logycaedx'
    _description = "Partner Logyca EDX"

    config_discount_id = fields.Many2one('config.discount.logycaedx', string='Discount', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Partner', tracking=True)
    year = fields.Integer(string='Año', required=True)

    def name_get(self):
        return [(logycaedx.id, '%s - %s' % (logycaedx.config_discount_id.name, logycaedx.partner_id.name)) for logycaedx in self]

    @api.model
    def create(self, values):
        if values.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id', '=', values.get('partner_id', False))])
            if partner_id:
                partner_id.write({'logycax_discount_id': values.get('config_discount_id', False)})
        return super(PartnerLogycaEDX, self).create(values)        

    def write(self, values):
        if values.get('partner_id', False):
            partner_id = self.env['res.partner'].search([('id', '=', values.get('partner_id', False))])
            if partner_id:
                partner_id.write({'logycax_discount_id': self.config_discount_id.id})
                self.partner_id.write({'logycax_discount_id': None})
        return super(PartnerLogycaEDX, self).write(values)