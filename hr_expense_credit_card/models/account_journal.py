# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_support_document = fields.Boolean(
        string='Diario de Documento Soporte',
        default=False,
        help='Marque esta opción si este diario debe usarse para documentos soporte en reportes de gastos. '
             'Cuando un reporte de gastos se contabilice como documento soporte, se usará este diario y '
             'la CXP se generará al proveedor de cada línea de gasto en lugar de al banco o tarjeta de crédito.'
    )
