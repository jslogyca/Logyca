# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class CRMLead(models.Model):
    _inherit = 'crm.lead'

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_two_id = fields.Many2one('product.product', string='Product Opt', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account',
        index=True, compute="_compute_analytic_account_id", store=True, readonly=False, check_company=True, copy=True)
        
    @api.depends('product_id', 'partner_id')
    def _compute_analytic_account_id(self):
        for record in self:
            analytic = self.env['account.analytic.default'].search([('product_id', '=', record.product_id.id,)], 
                                    order="id asc", limit=1)
            if analytic:
                record.analytic_account_id = analytic.analytic_id
