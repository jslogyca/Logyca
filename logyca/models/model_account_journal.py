# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


import logging
_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    x_resolution_number = fields.Char('Nro. Resolución')

    @api.constrains('x_resolution_number')
    def _check_resolution_number(self):
        for check in self:
            if check.x_resolution_number and not re.match(r'^[0-9]+$', check.x_resolution_number):
                raise ValidationError(_('El Nro. de Resolución debe contener sólo números.'))