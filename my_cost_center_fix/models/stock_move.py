from odoo import models

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _account_entry_move(self):
        account_move = super()._account_entry_move()

        for move in self:
            # Buscar la cuenta analítica desde la línea de venta relacionada
            analytic_account = False
            if move.sale_line_id and move.sale_line_id.analytic_account_id:
                analytic_account = move.sale_line_id.analytic_account_id

            if analytic_account:
                # Agregar la cuenta analítica solo en la línea de costo
                for line in move.account_move_ids.line_ids:
                    if line.account_id.id == move.product_id.categ_id.property_stock_account_out_id.id:
                        line.analytic_account_id = analytic_account.id

        return account_move
