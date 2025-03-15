# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import datetime


class x_api_gateway(models.Model):
    _name = 'logyca.api_gateway'
    _description = 'Movimientos API'

    method = fields.Char(string='Método', required=True)
    send_date = fields.Char(string='Fecha envió', compute='_send_date', store=True,required=True)    
    send_json = fields.Text(string='Json')    
    x_return = fields.Text(string='Respuesta')
    cant_attempts = fields.Integer(string='Cantidad de intentos')
    
    @api.depends('method')
    def _send_date(self):
        send_date = fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now())
        self.send_date = str(send_date)
