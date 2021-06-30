# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class AgreementRVC(models.Model):
    _name = 'agreement.rvc'
    _description = 'Agreement RVC'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean('Activo', default=True)