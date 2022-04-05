# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, AccessError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_draft(self):
        if not self.env.user.has_group('account_logyca.group_manager_move_cancel'):
            raise ValidationError(_('You do not have permissions to do this operation'))
        return super(AccountMove, self).button_draft()
