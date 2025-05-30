from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    deferred_expense_account_id = fields.Many2one("account.account", string="Cuenta de gasto diferido")
    deferred_revenue_account_id = fields.Many2one("account.account", string="Cuenta de ingreso diferido")
    deferred_expense_journal_id = fields.Many2one("account.journal", string="Diario de gasto diferido")
    deferred_revenue_journal_id = fields.Many2one("account.journal", string="Diario de ingreso diferido")
