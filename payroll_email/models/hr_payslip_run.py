# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    
    user_id = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    flag  = fields.Boolean('Flag',default=False)
    date_send = fields.Datetime('Send Date')

    def action_my_payslip_sent(self):
        """ Action to send Payroll through Email."""
        self.ensure_one()
        template = self.env.ref('payroll_email.email_template_for_my_payroll')        
        if self.slip_ids and template:
            for slip_id in self.slip_ids:
                slip_id.action_my_payslip_sent()
                self.flag = True
                self.date_send = fields.Date.today()
