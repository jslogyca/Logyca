# -*- coding: utf-8 -*-
import time
import babel
from odoo import models, fields, api, tools, _
from datetime import datetime


class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Installment", help="Loan installment")
    loan_id = fields.Many2one('hr.loan', string="Loan", help="Loan")


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_inputs_amount_loan(self, contract_id, date_from, date_to, type_compute):
        self._cr.execute(''' SELECT h.loan_amount, h.payment_date, i.id, i.code, i.name, h.id
                                FROM hr_loan h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s
                                AND h.type_compute = %s
                                AND h.state = %s AND 
                                h.payment_date between %s and %s ''',(contract_id.id, type_compute, 'approve', date_from, date_to))
        loan_amount = self._cr.fetchall()
        return loan_amount  

    def get_inputs_fijo_loan(self, contract_id, type_compute):
        self._cr.execute(''' SELECT h.loan_amount, h.payment_date, i.id, i.code, i.name, h.id
                                FROM hr_loan h
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s
                                AND h.type_compute = %s
                                AND h.state = %s ''',(contract_id.id, type_compute, 'approve'))
        loan_amount = self._cr.fetchall()
        return loan_amount
        
    def get_inputs_amount_loan_line(self, contract_id, date_from, date_to, type_compute):
        self._cr.execute(''' SELECT l.amount, l.date, i.code, i.id, i.name, h.id, l.id
                                FROM hr_loan_line l
                                INNER JOIN hr_loan h ON h.id = l.loan_id
                                INNER JOIN hr_payslip_input_type i ON i.id=h.input_id
                                WHERE h.contract_id=%s
                                AND h.type_compute = %s
                                AND h.state = %s
                                and l.date between %s and %s ''',(contract_id.id, type_compute, 'approve', date_from, date_to))
        loan_amount = self._cr.fetchall()
        return loan_amount

    def _get_input_line(self):
        """This Compute the other inputs to employee payslip.
                           """
        print('*******************---------------')
        res = super(HrPayslip, self)._get_input_line()
        print('*******************--------------- 111111', res)
        if self.employee_id and self.contract_id:
            # LOAN AMOUNT
            loan_amount = self.get_inputs_amount_loan(self.contract_id, self.date_from, self.date_to, 'amount')
            # LOAN FIJO
            loan_amount += self.get_inputs_fijo_loan(self.contract_id, 'fijo')
            # LOAN LINE
            loan_line = self.get_inputs_amount_loan_line(self.contract_id, self.date_from, self.date_to, 'fee')
        else:
            loan_amount = []
            loan_line = []
        print('*******************--------------- 22222222', loan_amount)
        for result in res:
            for input in loan_amount:
                if result.get('input_type_id') == input[2]:
                    result['amount'] = input[0]
                    result['loan_id'] = input[5]
                    
            for input in loan_line:
                if result.get('code') == input[2]:
                    result['amount'] = input[0]
                    result['loan_id'] = input[5]
                    result['loan_line_id'] = input[6]
        return res

    def _get_new_worked_days_lines(self):
        if self.struct_id.use_worked_day_lines:
            # computation of the salary worked days
            worked_days_line_values = self._get_worked_day_lines()
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_values:
                worked_days_lines |= worked_days_lines.new(r)
            return worked_days_lines
        else:
            return [(5, False, False)]

    def action_payslip_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = True
                line.loan_line_id.payslip_id = self.id
                line.loan_line_id.loan_id._compute_loan_amount()
                line.loan_line_id.loan_id._compute_line_done()
            if line.loan_id:
                line.loan_id.payslip_id = self.id
                if line.loan_id.type_compute == 'amount':
                     line.loan_id.state = 'done'
                if line.loan_id.type_compute == 'fijo':
                    move_obj = self.env['hr.loan.line'].create({
                        'date': self.date_to,
                        'employee_id': self.employee_id.id,
                        'amount': line.loan_id.loan_amount,
                        'paid': True,
                        'loan_id': line.loan_id.id,
                        'payslip_id': self.id,

                    })                    
                line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_done()

    def action_payslip_cancel_done(self):
        for line in self.input_line_ids:
            if line.loan_line_id:
                line.loan_line_id.paid = False
                line.loan_line_id.payslip_id = None
                line.loan_line_id.loan_id._compute_loan_amount()
                line.loan_line_id.loan_id._compute_line_done()
            if line.loan_id:
                if line.loan_id.type_compute == 'amount':
                    line.loan_id.payslip_id = None
                    line.loan_id.state = 'approve'
                if line.loan_id.type_compute == 'fijo':
                    line_ids = self.env['hr.loan.line'].search([('paid', '=', True), ('payslip_id', '=', self.id)]).unlink()
                line.loan_id._compute_loan_amount()
        return super(HrPayslip, self).action_payslip_cancel_done()
