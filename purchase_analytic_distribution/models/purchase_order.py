from odoo import models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            for line in order.order_line:
                for move in line.move_ids:
                    if line.analytic_distribution:
                        move.analytic_distribution = line.analytic_distribution
        return res
