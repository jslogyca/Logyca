# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class LogImportRVC(models.Model):
    _name = 'log.import.rvc'
    _description = 'Log Import RVC'
    _rec_name = 'name'

    name = fields.Text(string='Name')
    date_init = fields.Datetime(string='Fecha de Importación')
    user_id = fields.Many2one('res.users', string='Users')
    

    