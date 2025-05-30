# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools.translate import _

DOC_TYPE = [
    ('invoice', 'Invoices'),
    ('invoice_export', 'Invoice Export'),
    ('type03', 'Tipo 03'),
    ('type04', 'Tipo 04'),
    ('credit_note', 'Credit Notes'),
    ('debit_note', 'Debit Notes'),
    ('ds', 'Documento soporte en adquisiciones'),
    ('nds', 'Nota de ajuste Documento soporte en adquisiciones'),
    ('event', 'Events')
]

EVENT_TYPE = [
    ('02', 'Documento electrónico tipo ApplicationResponse'),
    ('04', 'Documento electrónico tipo ApplicationResponse '
           '– Documento Rechazado por la DIAN'),
    ('030', 'Documento electrónico tipo ApplicationResponse '
            '‐ Acuse de recibo de Factura Electrónica de Venta'),
    ('031', 'Documento electrónico tipo ApplicationResponse '
            '‐ Reclamo de la Factura Electrónica de Venta'),
    ('032', 'Documento electrónico tipo ApplicationResponse '
            '‐ Recibo del bien o prestación del servicio'),
    ('033', 'Documento electrónico tipo ApplicationResponse '
            '‐ Aceptación expresa'),
    ('034', 'Documento electrónico tipo ApplicationResponse '
            '‐ Aceptación Tácita')
    ]


class TypeEDocument(models.Model):
    _name = 'type.edocument'
    _description = 'Type EDocument'
    _order = "name asc"

    # 13.1.3 DIAN Tipo de Documento
    name = fields.Char('Name', size=120)
    ecode = fields.Char('DIAN Code', required=True, default='01')
    display_type = fields.Selection(selection=[
        ('document', 'Document'),
        ('event', 'Event'),
    ], string="", default='document')
    document_type = fields.Selection(selection=DOC_TYPE,
                                     string='Document Type',
                                     help='Documentos requeridos por la DIAN')
    code_prefix_file = fields.Char('Document Code Prefix',
                                   help="Nombre del Archivo xml")
    sequence_id = fields.Many2one('ir.sequence',
                                  string='Secuencia nombre XML')
