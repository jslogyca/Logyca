# -*- coding: utf-8 -*-

from odoo import api,fields, models

class PayslipMassMail(models.TransientModel):
    _name="payroll.mass.mail"
    _description = 'Payslip Mass Mail'
    
    payslip_ids = fields.Many2many('hr.payslip',string="Payslips",required=True)
   
# function to send mass Payslip
    def send_mass_ps_mail(self):
        values = self.payslip_ids
        for plp in values:
            email_action = plp.action_my_payslip_sent()
            if email_action and email_action.get('context'):
                email_ctx = email_action['context']
                email_ctx.update(default_email_from=values.company_id.email)
                plp.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))  
        return True

    def send_mass_iyr_mail(self):
        values = self.payslip_ids
        for plp in values:
            email_action = plp.action_my_iyr_sent()
            if email_action and email_action.get('context'):
                email_ctx = email_action['context']
                email_ctx.update(default_email_from=values.company_id.email)
                plp.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))  
        return True