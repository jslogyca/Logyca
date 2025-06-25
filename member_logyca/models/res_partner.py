# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def activ_member_tyb(self):
        return {
            'name': 'Activar Membresía TYB',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': self.env.ref('member_logyca.member_tyb_wizard_view_form').id,
            'res_model': 'member.tyb.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': self._context
        }
