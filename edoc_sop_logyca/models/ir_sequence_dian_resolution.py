# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class IrSequenceDianResolution(models.Model):
    _name = 'ir.sequence.dian_resolution'
    _description = "Ir Sequence Dian Resolution"
    _order = "date_from desc"

    def _get_number_next_actual(self):
        for element in self:
            element.number_next_actual = element.number_next

    def _set_number_next_actual(self):
        for record in self:
            record.write({'number_next': record.number_next_actual or 0})

    @api.depends('from_range')
    def _get_initial_number(self):
        for record in self:
            if not record.number_next:
                record.number_next = record.from_range

    resolution_number = fields.Char('Resolution number', required=True, size=16)
    resolution_date = fields.Datetime('Resolution Date', required=True)
    resolution_prefix = fields.Char('Resolution prefix', required=True, size=4)
    from_range = fields.Integer('Initial Range', required=True)
    to_range = fields.Integer('Final Range', required=True)    
    date_from = fields.Date('From Date', required=True)
    date_to = fields.Date('To Date', required=True)
    technical_key = fields.Char('Technical Key', size=64)
    active_resolution = fields.Boolean('Active resolution', required=False, default=True)
    number_next = fields.Integer('Next Number', compute='_get_initial_number', store=True)
    number_next_actual = fields.Integer(compute='_get_number_next_actual', inverse='_set_number_next_actual',
                                 string='Next Number', required=True, default=1, help="Next number of this sequence")    
    sequence_id = fields.Many2one("ir.sequence", 'Main Sequence', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', required=True,
        default=lambda self: self.env['res.company']._company_default_get('account.account'))
    xml_envio = fields.Text(string='XML Eviado')
