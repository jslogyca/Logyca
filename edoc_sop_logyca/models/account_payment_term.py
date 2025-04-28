# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class AccountPaymentTerm(models.Model):
    _inherit= 'account.payment.term'

    einvice_form_payment_id = fields.Many2one('form.payment.einvoice', string='form payment einvoice')
