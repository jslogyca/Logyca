# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    use_dian_control = fields.Boolean('Use DIAN resolutions')
    dian_resolution_ids = fields.One2many('ir.sequence.dian_resolution', 'sequence_id', 'DIAN Resolutions')

    @api.constrains('dian_resolution_ids')   
    def val_active_resolution(self):  
        _active_resolution = 0
        if self.use_dian_control:
            for record in self.dian_resolution_ids:
                if record.active_resolution:
                    _active_resolution += 1
            if _active_resolution > 1:
                raise ValidationError( _('The system needs only one active DIAN resolution') )
            if _active_resolution == 0:
                raise ValidationError( _('The system needs at least one active DIAN resolution') )