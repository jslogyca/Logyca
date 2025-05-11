# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class x_rvc_information(models.Model):
    _name = 'logyca.rvc_information'
    _description = 'RVC Information'
    
    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    types = fields.Selection([('1', 'Logyca / COLABORA'),
                              ('2', 'Logyca / ANALÍTICA'),
                              ('3', 'Derechos de identificación')], string='Servicio', required=True)
    activation_date = fields.Date(string="Fecha activación")    
    finally_date = fields.Date(string="Fecha finalización")