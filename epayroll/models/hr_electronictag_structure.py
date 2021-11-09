# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class HRElectronictagStructure(models.Model):
    _name= 'hr.electronictag.structure'
    _inherit = ['mail.thread']
    _description = "Electronic tag Structure"
    _order = "id asc"

    name = fields.Char('Name')
    ref = fields.Char('Ref')
    report = fields.Boolean('Report', default=False)
    parent_id = fields.Many2one('hr.electronictag.structure', string='Padre')
    type = fields.Selection([('devengados', 'Devengados'), 
                            ('deducciones', 'Deducciones'),
                            ('neto', 'Neto')], string='Tipo')
    type_extra = fields.Selection([('hora_extra', 'Hora Extra o Recargo'), 
                            ('incapacidad', 'Incapacidad')], string='Tipo Extra')
