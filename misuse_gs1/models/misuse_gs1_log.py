from odoo import models, fields

class MisuseGs1LogAttachment(models.Model):
    _name = 'misuse.gs1.log.attachment'
    _description = 'Attachment for Misuse GS1 Log'

    log_id = fields.Many2one('misuse.gs1.log', string='Log', required=True, ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    path = fields.Char(string='Path', required=True)

class MisuseGS1LogFollowUp(models.Model):
    _name = 'misuse.gs1.log.followup'
    _description = 'Follow-up for Misuse GS1 Log'

    log_id = fields.Many2one('misuse.gs1.log', string='Log', required=True, ondelete='cascade')
    comments = fields.Text(string='Comments', required=True)
    gs1_agent_email = fields.Char(string='GS1 Agent Email', required=True)

class MisuseGs1Log(models.Model):
    _name = 'misuse.gs1.log'
    _description = 'Misuse GS1 Log'

    partner_id = fields.Many2one('res.partner', string='Partner')
    case_id = fields.Char(string='Case ID', required=True)
    misuse_type = fields.Char(string='Misuse type')
    tracking_type = fields.Char(string='Tracking type')
    state = fields.Char(string='Case status')
    user_attachments = fields.One2many('misuse.gs1.log.attachment', 'log_id', string='User Attachments')
    date_start = fields.Date(string='Start date', required=True)
    date_end = fields.Date(string='End date', required=True)
    remaining_time = fields.Integer(string='Remaining Time (days)')
    follow_up = fields.One2many('misuse.gs1.log.followup', 'log_id', string='Follow-up')
