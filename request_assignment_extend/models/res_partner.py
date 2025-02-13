from odoo import fields, models

class ResPartner(models.Model):
    _inherit = 'res.partner'

    request_received_ids = fields.One2many(
        'request.partner.code.assignment',
        'partner_receiver_id',
        string='Request Partner Receiver'
    )
