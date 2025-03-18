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
    lost_alert = fields.Boolean('Lost Alert', default=False)


    @api.depends('product_id', 'partner_id')
    def _compute_analytic_account_id(self):
        for record in self:
            analytic = self.env['account.analytic.default'].search([('product_id', '=', record.product_id.id,)], 
                                    order="id asc", limit=1)
            if analytic:
                record.analytic_account_id = analytic.analytic_id

    def action_set_lost(self, **additional_values):
        stage_id = self._stage_find(domain=[('is_lose', '=', True)])
        """ Lost semantic: probability = 0 or active = False """
        result = self.write({'lost_alert':True, 'stage_id':stage_id.id, 'probability': 0, 'automated_probability': 0, **additional_values})
        # self._rebuild_pls_frequency_table_threshold()
        return result                  

    def toggle_active(self):
        """ When archiving: mark probability as 0. When re-activating
        update probability again, for leads and opportunities. """
        res = super(CRMLead, self).toggle_active()
        activated = self.filtered(lambda lead: lead.lost_alert)
        archived = self.filtered(lambda lead: not lead.lost_alert)
        if activated:
            activated.write({'lost_reason': False, 'lost_alert': False})
            activated._compute_probabilities()
        if archived:
            archived.write({'probability': 0, 'automated_probability': 0, 'lost_alert': False})
        return res

    @api.onchange('activity_ids')
    def validas_activity_ids(self):
        print('rrrrrrrrrrr')
        UUUUUUU
    