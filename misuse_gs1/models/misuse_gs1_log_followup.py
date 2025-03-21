from odoo import models, fields

class MisuseGS1LogFollowUp(models.Model):
    _name = 'misuse.gs1.log.followup'
    _description = 'Follow-up for Misuse GS1 Log'

    log_id = fields.Many2one('misuse.gs1.log', string='Log', required=True, ondelete='cascade')
    date_time = fields.Datetime(string='Date and Time', required=True, default=fields.Datetime.now)
    comments = fields.Text(string='Comments', required=True)
    gs1_agent_email = fields.Char(string='GS1 Agent Email', required=True)
