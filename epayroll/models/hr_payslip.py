# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero, pycompat
from odoo.addons import decimal_precision as dp
from odoo.osv import expression
from datetime import date,datetime
import logging
_logger = logging.getLogger(__name__)

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    pay_method_epayroll_id = fields.Many2one('payment.method.epayroll', string='Medios de Pago')
    pay_form_epayroll_id = fields.Many2one('payment.form.epayroll', string='Medios de Pago')
    type_epayroll_id = fields.Many2one('type.epayroll', string='Tipo')
