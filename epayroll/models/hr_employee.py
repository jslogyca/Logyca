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

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    sub_job_id = fields.Many2one('hr.sub.type.job', string='Tipo')
    ejob_id = fields.Many2one('hr.type.ejob', string='Type Job')