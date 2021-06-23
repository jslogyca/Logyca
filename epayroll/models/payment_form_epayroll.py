# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class PaymentFormEPayroll(models.Model):
    _name = 'payment.form.epayroll'
    _description = 'Payment Form EPayroll'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')

#