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
        index=True, readonly=False, check_company=True, copy=True, compute="_compute_analytic_account_id", store=True,)
    day_close_alert = fields.Boolean(default=False, index=True, compute="compute_days_close")
    lost_alert = fields.Boolean('Lost Alert', default=False)
    day_close_line = fields.Float('Days to Close', compute='compute_days_close', store=True)
    days_exceeded = fields.Float(string='Días de cierre excedidos', compute='compute_days_close', store=True)    

    @api.depends('create_date', 'date_closed', 'date_deadline', 'day_close_alert')
    def compute_days_close(self):
        for lead in self:
            if lead.date_deadline:
                dt_create = fields.Datetime.from_string(lead.create_date)
                dt_close = fields.Datetime.from_string(lead.date_deadline)
                close_date = fields.Date.to_date(lead.date_deadline)
                today = fields.Date.context_today(lead)
                delta = dt_close - dt_create
                lead.day_close = abs(delta.days) + 2
                lead.day_close_line = abs(delta.days) + 2
                lead.day_close_alert = True
                delta_exc = (today - close_date).days + 2
                lead.days_exceeded = delta_exc if delta_exc > 0 else 0
            if lead.date_closed:
                dt_create = fields.Datetime.from_string(lead.create_date)
                dt_close = fields.Datetime.from_string(lead.date_closed)
                close_date = fields.Date.to_date(lead.date_closed)
                today = fields.Date.context_today(lead)
                delta = dt_close - dt_create
                lead.day_close = abs(delta.days) + 2
                lead.day_close_line = abs(delta.days) + 2
                lead.day_close_alert = True
                delta_exc = (today - close_date).days + 2
                lead.days_exceeded = delta_exc if delta_exc > 0 else 0

    @api.depends('product_id', 'partner_id', 'analytic_account_id')
    def _compute_analytic_account_id(self):
        for record in self:
            analytic = self.env['account.analytic.distribution.model'].search([('product_id', '=', record.product_id.id,)], 
                                    order="id asc", limit=1)
            if analytic:
                dist = analytic.analytic_distribution or {}
                key_str = next(iter(dist.keys()))
                if dist:
                    key_str = next(iter(dist.keys()))
                    analytic = self.env['account.analytic.account'].search([('id', '=', int(key_str),)], 
                                            order="id asc", limit=1)                    
                    record.analytic_account_id = analytic.id
                else:
                    record.analytic_account_id = False

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

    @api.model
    def message_post(self, **kwargs):
        # Publica normalmente
        msg = super().message_post(**kwargs)
        # kwargs suele traer: model, res_id, ...
        # Si es un mensaje sobre este lead, actualizamos
        if kwargs.get('model') == 'crm.lead' and kwargs.get('res_id') == self.id:
            self.write({
                'date_follow': fields.Date.context_today(self),
            })
        return msg
