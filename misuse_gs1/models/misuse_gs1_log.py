from odoo import models, fields, api


class MisuseGs1Log(models.Model):
    _name = 'misuse.gs1.log'
    _description = 'Misuse GS1 Log - trazabilidad del mal uso del sistema GS1'

    partner_id = fields.Many2one('res.partner', string='Partner')
    case_id = fields.Char(string='Case ID', required=True)
    misuse_type = fields.Char(string='Misuse type', description='Misuse type')
    tracking_type = fields.Char(string='Tracking type', description='Tracking type')
    state = fields.Char(string='Case status', description='Case status')
    user_attachments = fields.One2many('misuse.gs1.log.attachment', 'log_id', string='User Attachments')
    date_start = fields.Date(string='Start date', required=True)
    date_end = fields.Date(string='End date', required=True)
    remaining_time = fields.Integer(string='Remaining Time (days)')
    prefixes = fields.Char(string='Prefixes')

class MisuseGs1LogAttachment(models.Model):
    _name = 'misuse.gs1.log.attachment'
    _description = 'Attachment for Misuse GS1 Log'

    log_id = fields.Many2one('misuse.gs1.log', string='Log', required=True, ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    path = fields.Char(string='Path', required=True)
