# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def get_partner_type(self, type_reg_contribution):
        if type_reg_contribution == 'eps':
            return self.slip_id.employee_id.partner_eps
        elif type_reg_contribution == 'fond_pens':
            return self.slip_id.employee_id.partner_fond_pens
        elif type_reg_contribution == 'fond_censa':
            return self.slip_id.employee_id.partner_fond_censa
        elif type_reg_contribution == 'arl':
            return self.slip_id.employee_id.partner_arl
        else:
            return self.slip_id.employee_id.partner_caja

    def _get_partner_id(self, credit_account):
        """
        Get partner_id of slip line to use in account_move_line
        """
        # use partner of salary rule or fallback on employee's address
        register_partner_id = None
        if credit_account:
            if self.salary_rule_id.register_credit_id.type_reg_contribution:
                register_partner_id = self.get_partner_type(self.salary_rule_id.register_credit_id.type_reg_contribution)

            if not register_partner_id:
                register_partner_id = self.salary_rule_id.register_credit_id.partner_id
        else:
            if self.salary_rule_id.register_id.type_reg_contribution:
                register_partner_id = self.get_partner_type(self.salary_rule_id.register_id.type_reg_contribution)

            if not register_partner_id:
                register_partner_id = self.salary_rule_id.register_id.partner_id

        partner_id = (
            register_partner_id.id or self.slip_id.employee_id.address_home_id.id
        )
        if credit_account:
            if (
                register_partner_id
                or self.salary_rule_id.account_credit.internal_type
                in ("receivable", "payable")
            ):
                return partner_id
        else:
            if (
                register_partner_id
                or self.salary_rule_id.account_debit.internal_type
                in ("receivable", "payable")
            ):
                return partner_id
        return False
