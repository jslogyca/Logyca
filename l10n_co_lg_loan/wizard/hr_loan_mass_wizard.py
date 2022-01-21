# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import date_utils

import base64


class HRLoanMassWizard(models.TransientModel):
    _name = 'hr.loan.mass.wizard'
    _description = 'HR Loan Mass Wizard'

    state = fields.Selection([('draft', 'Draft'),
                                ('waiting_approval_1', 'Submitted'),
                                ('approve', 'Approved'),
                                ('refuse', 'Refused'),
                                ('cancel', 'Canceled'),
                                ('done', 'Done')], string="State", default='draft', )
    
    def change_state_loan(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        loan_ids = self.env['hr.loan'].browse(active_ids)
        for loan in loan_ids:
            if self.state=='draft':
                loan.action_draft()
            elif self.state=='waiting_approval_1':
                loan.action_submit()
            elif self.state=='approve':
                loan.action_approve()
            elif self.state=='refuse':
                loan.action_refuse()
            elif self.state=='cancel':
                loan.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
