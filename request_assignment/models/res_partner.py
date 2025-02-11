# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    request_assignment_ids = fields.One2many('request.partner.code.assignment', 'partner_id', string='Request Assignment')
    #request_received_ids = fields.One2many('request.partner.code.assignment', 'partner_receiver', string='Request Partner Receiver')
