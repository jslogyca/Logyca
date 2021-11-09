# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class DianEpayslipBug(models.Model):
    _name = 'dian.epayslip.bug'
    _description = 'Dian Epayslip Bug'
    _order = 'id desc'

    epayslip_bach_id = fields.Many2one('epayslip.bach', string='Epayslip bach', readonly=True)
    code = fields.Char(string=u'Código')
    type = fields.Selection([('sent', 'Envíado'),
                                ('response', 'Respuesta')], required=True, default='response')
    description = fields.Char(string='Descripción', required=True, readonly=True)

#