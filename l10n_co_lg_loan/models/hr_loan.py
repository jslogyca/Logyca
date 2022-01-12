# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        if result['employee_id']:
            result['contract_id'] = self.env['hr.contract'].search([('employee_id', '=', result['employee_id']), ('state','=','open')], limit=1).id
        return result

    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            loan.total_amount = loan.loan_amount
            loan.balance_amount = balance_amount
            loan.total_paid_amount = total_paid

    def _compute_line_done(self):
        for loan in self:
            if loan.type_compute != 'fijo':
                lines = loan.loan_lines.filtered(lambda line: line.paid == False and not line.payslip_id)
                if not lines:
                    self.write({'state': 'done'})
                else:
                    self.write({'state': 'approve'})

    name = fields.Char(string="Loan Name", default="/", readonly=True, help="Name of the loan")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    contract_id = fields.Many2one('hr.contract', string="Contract", required=True, help="Employee Contract")
    input_id = fields.Many2one('hr.payslip.input.type', string='Input',tracking=True)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "paymemt")
    done_date = fields.Date(string="Payment Done Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "Done")
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position",
                                   help="Job position")
    loan_amount = fields.Float(string="Loan Amount", required=True, help="Loan amount")
    loan_total = fields.Float(string="Loan Total", help="Loan Total", default=0.0)
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_loan_amount',
                                help="Total loan amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_loan_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_loan_amount',
                                     help="Total paid amount")
    state = fields.Selection([('draft', 'Draft'),
                                ('waiting_approval_1', 'Submitted'),
                                ('approve', 'Approved'),
                                ('refuse', 'Refused'),
                                ('cancel', 'Canceled'),
                                ('done', 'Done'),
                            ], string="State", default='draft', track_visibility='onchange', copy=False, )
    type_compute = fields.Selection([('fijo', 'Fijo'),
                                        ('amount', 'Amount'),
                                        ('fee', 'Fee')], string="Compute Type", track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Account Analytic', tracking=True)
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")

    @api.model
    def create(self, values):
        loan_count = self.env['hr.loan'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        # if loan_count:
        #     raise ValidationError(_("The employee has already a pending installment"))
        # else:
        values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        res = super(HrLoan, self).create(values)
        self._compute_loan_amount()
        return res

    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.filtered(lambda line: line.paid == False).unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            if loan.type_compute == 'fee':
                loan._compute_loan_amount()
                loan.installment = ((loan.loan_amount - loan.total_paid_amount) / loan.loan_total)
                amount = loan.loan_total
                for i in range(1, loan.installment + 1):
                    self.env['hr.loan.line'].create({
                        'date': date_start,
                        'amount': amount,
                        'employee_id': loan.employee_id.id,
                        'loan_id': loan.id})
                    date_start = date_start + relativedelta(months=1)
            loan._compute_loan_amount()
        return True

    def action_refuse(self):
        if self.state in ('draft', 'waiting_approval_1'):
            self._compute_loan_amount()
            return self.write({'state': 'refuse'})

    def action_done(self):
        self._compute_loan_amount()
        self.done_date = fields.Date.today()
        return self.write({'state': 'done'})

    def action_draft(self):
        if data.state == 'cancel':
            if self.type_compute != 'fijo' and self.loan_lines:
                lines = self.loan_lines.filtered(lambda line: line.paid == False).unlink()
            return self.write({'state': 'draft'})

    def action_submit(self):
        if self.state in ('draft'):
            self._compute_loan_amount()
            self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        if self.state in ('draft'):
            self._compute_loan_amount()
            self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if data.state == 'waiting_approval_1':
                data._compute_loan_amount()
                if not data.loan_lines and data.type_compute not in ('fijo', 'amount'):
                    raise ValidationError(_("Please Compute installment"))
                else:
                    self.write({'state': 'approve'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            contract_id = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id), ('state','=','open')], limit=1).id
            self.contract_id = contract_id
            # if not contract_id:
            #     raise UserError(_("The employee %s is not contract active") % self.employee_id.name)


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    loan_id = fields.Many2one('hr.loan', string="Loan Ref.", help="Loan")
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", help="Payslip")


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        # self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])
        self.loan_count = len(self.loan_ids)

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
    loan_ids = fields.One2many('hr.loan', 'employee_id', string='Employee Loans', copy=False, domain=[('state','in',('done', 'approve'))])


class HrContract(models.Model):
    _inherit = "hr.contract"

    loan_ids = fields.One2many('hr.loan', 'contract_id', string='Loan Request', copy=False, readonly=True, 
                                        domain=[('type_compute', '=', 'fijo'), ('state','in',('done', 'approve'))], states={'draft': [('readonly', False)]})
