from odoo import models

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_deferred_account_and_journal(self, is_expense=True):
        self.ensure_one()
        product = self.product_id
        account = journal = None

        if product:
            if is_expense:
                account = product.deferred_expense_account_id or self.company_id.deferred_expense_account_id
                journal = product.deferred_expense_journal_id or self.company_id.deferred_journal_id
            else:
                account = product.deferred_revenue_account_id or self.company_id.deferred_revenue_account_id
                journal = product.deferred_revenue_journal_id or self.company_id.deferred_journal_id

        return account, journal
