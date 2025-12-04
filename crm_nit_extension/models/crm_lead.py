# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    nit = fields.Char(
        string='NIT',
        help='Número de Identificación Tributaria de la empresa',
        tracking=True,
    )
    agent_call = fields.Boolean('Agent Call', default=False)
    sent_agent = fields.Boolean('Sent Agent Call', default=False)
    date_sent_agent = fields.Date(string='Date Sent Agent Call')    
