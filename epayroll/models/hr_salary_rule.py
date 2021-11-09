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

class HRSalaryRule(models.Model):
    _inherit= 'hr.salary.rule'

    electronictag_id = fields.Many2one('hr.electronictag.structure', string='Electronic Tags')
    type_extra = fields.Selection(related='electronictag_id.type_extra', string='Tipo Extra')
    porcentaje_hora_extra = fields.Float('Porcentaje Hora Extra')
    type_incapacidad_id = fields.Many2one('hr.tipo.incapacidad.dian', string='Tipo de Incapacidad')
