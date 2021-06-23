# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class PaymentMethodEPayroll(models.Model):
    _name = 'payment.method.epayroll'
    _description = 'Payment Method EPayroll'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#