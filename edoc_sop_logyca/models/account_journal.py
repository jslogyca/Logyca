# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    einvoice_journal = fields.Boolean('eInvoice Journal', default=False)
    type_document_id = fields.Many2one('type.edocument', string='Documentos requeridos por la DIAN', required=False)
