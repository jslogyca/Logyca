# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api


class PayrollInheritsMail(models.Model):
    _inherit = 'hr.payslip'
    
    user_id = fields.Many2one('res.users','Current User', default=lambda self: self.env.user)
    flag  = fields.Boolean('Flag',default=False)
    date_send = fields.Datetime('Send Date')

    def view_mass_payroll_wizard(self):
        payslip_ids = []
        active_ids = self.env.context.get('active_ids',[])
        psp_id = self.env['hr.payslip'].search([('id','in',active_ids)])
        for rec in psp_id:
            if rec.flag == False:
                payslip_ids.append(rec.id)   
        vals = ({'default_payslip_ids':payslip_ids})
        return {
            'name':"Send Mass Payslips by Mail",
            'type': 'ir.actions.act_window', 
            'view_type': 'form', 
            'view_mode': 'form',
            'res_model': 'payroll.mass.mail', 
            'target': 'new', 
            'context': vals,
            }

    def action_my_payslip_sent(self):
        """ Action to send Payroll through Email."""
        self.ensure_one()
        template = self.env.ref('payroll_email.email_template_for_my_payroll')
        if template:
            self.env['mail.template'].browse(template.id).send_mail(self.id,force_send=True)
            self.flag = True
            self.date_send = fields.Date.today()