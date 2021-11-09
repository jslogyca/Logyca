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

class HrContract(models.Model):
    _inherit= 'hr.contract'

    periodo_nomina = fields.Selection([('1', 'Semanal'), 
                                        ('2', 'Decenal'),
                                        ('3', 'Catorcenal'),
                                        ('4', 'Quincenal'),
                                        ('5', 'Mensual'),
                                        ('6', 'Otro')], string='Periodo de Nómina', default='5')
