# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _

from odoo.exceptions import UserError, ValidationError

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    budget_group_id = fields.Many2one('logyca.budget_group', string='Budget Group')
    name_move = fields.Char('Move Name')

    @api.onchange('contract_id', 'employee_id')
    def _onchange_contract_id(self):
        if self.employee_id:
            self.budget_group_id = self.employee_id.budget_group_id

    def get_account_salary(self, analytic_account_id, salary_rule_id, type_account):
        type_account_id = None
        if analytic_account_id and analytic_account_id.type_id:
            type_account_id = self.env['hr.analytic.type.line'].search([('salary_rule_id', '=', salary_rule_id.id), ('analytic_type_id', '=', analytic_account_id.type_id.id),
                                                                                ('type_account', '=', type_account), ('company_id', '=', self.company_id.id)], 
                                                                                    order="id asc", limit=1)
        if type_account_id:
            return type_account_id.account_id.id
        else:
            type_account_id = self.env['hr.analytic.type.line'].search([('company_id', '=', self.company_id.id), ('salary_rule_id', '=', salary_rule_id.id), ('type_account', '=', type_account)], order="id asc", limit=1)            
            if type_account_id:
                return type_account_id.account_id.id
            else:
                return

    def action_payslip_done(self):
        res = super(HrPayslip, self).action_payslip_done()

        for slip in self:
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            date = slip.date or slip.date_to
            currency = (
                slip.company_id.currency_id or slip.journal_id.company_id.currency_id
            )

            name = _("Payslip of %s") % (slip.employee_id.name)
            move_dict = {
                "narration": name,
                "ref": slip.number,
                "journal_id": slip.journal_id.id,
                "date": date,
                "partner_id": slip.employee_id.address_home_id.id,
            }
            for line in slip.line_ids:
                amount = currency.round(slip.credit_note and -line.total or line.total)
                if currency.is_zero(amount):
                    continue

                analytic_salary_id = slip.budget_group_id.id or slip.employee_id.budget_group_id.id
                analytic_slip_id = slip.budget_group_id or slip.employee_id.budget_group_id

                debit_account_id = self.get_account_salary(analytic_slip_id, line.salary_rule_id, 'debit')
                credit_account_id = self.get_account_salary(analytic_slip_id, line.salary_rule_id, 'credit')
                account_id = debit_account_id or credit_account_id
                tax_ids = False
                tax_tag_ids = False

                tax_repartition_line_id = False
                if debit_account_id:
                    debit_line = (
                        0,
                        0,
                        {
                            "name": line.name,
                            "partner_id": line._get_partner_id(credit_account=False)
                            or slip.employee_id.address_home_id.id,
                            "account_id": debit_account_id,
                            "journal_id": slip.journal_id.id,
                            "date": date,
                            "debit": amount > 0.0 and amount or 0.0,
                            "credit": amount < 0.0 and -amount or 0.0,
                            "x_budget_group": analytic_salary_id,
                            "tax_line_id": False,
                            "tax_ids": tax_ids,
                            "tax_repartition_line_id": tax_repartition_line_id,
                        },
                    )
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]["debit"] - debit_line[2]["credit"]

                if credit_account_id:
                    credit_line = (
                        0,
                        0,
                        {
                            "name": line.name,
                            "partner_id": line._get_partner_id(credit_account=True)
                            or slip.employee_id.address_home_id.id,
                            "account_id": credit_account_id,
                            "journal_id": slip.journal_id.id,
                            "date": date,
                            "debit": amount < 0.0 and -amount or 0.0,
                            "credit": amount > 0.0 and amount or 0.0,
                            "x_budget_group": analytic_salary_id,
                            "tax_line_id": False,
                            "tax_ids": tax_ids,
                            "tax_repartition_line_id": tax_repartition_line_id,
                        },
                    )
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]["credit"] - credit_line[2]["debit"]

            if currency.compare_amounts(credit_sum, debit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _(
                            'The Expense Journal "%s" has not properly '
                            "configured the Credit Account!"
                        )
                        % (slip.journal_id.name)
                    )
                adjust_credit = (
                    0,
                    0,
                    {
                        "name": _("Adjustment Entry"),
                        "partner_id": slip.employee_id.address_home_id.id,
                        "account_id": acc_id,
                        "journal_id": slip.journal_id.id,
                        "date": date,
                        "debit": 0.0,
                        "credit": currency.round(debit_sum - credit_sum),
                    },
                )
                line_ids.append(adjust_credit)

            elif currency.compare_amounts(debit_sum, credit_sum) == -1:
                acc_id = slip.journal_id.default_account_id.id
                if not acc_id:
                    raise UserError(
                        _(
                            'The Expense Journal "%s" has not properly '
                            "configured the Debit Account!"
                        )
                        % (slip.journal_id.name)
                    )
                adjust_debit = (
                    0,
                    0,
                    {
                        "name": _("Adjustment Entry"),
                        "partner_id": slip.employee_id.address_home_id.id,
                        "account_id": acc_id,
                        "journal_id": slip.journal_id.id,
                        "date": date,
                        "debit": currency.round(credit_sum - debit_sum),
                        "credit": 0.0,
                    },
                )
                line_ids.append(adjust_debit)
            move_dict["line_ids"] = line_ids
            move = self.env["account.move"].create(move_dict)
            slip.write({"move_id": move.id, "date": date})
            move.post()
            if not slip.name_move:
                slip.name_move = move.name
            else:
                move.write({'name': slip.name_move})
                move.journal_id.sequence_id.write({'number_next_actual': (move.journal_id.sequence_id.number_next_actual-1)})
        return res

    def action_payslip_cancel_done(self):
        moves = self.mapped("move_id")
        moves.filtered(lambda x: x.state == "posted").button_cancel()
        moves.filtered(lambda x: x.state == "cancel").button_draft()
        self._cr.execute('DELETE FROM account_move WHERE id = %s', (moves.id,))
        return super(HrPayslip, self).action_payslip_cancel_done()        

