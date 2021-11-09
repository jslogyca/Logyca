# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _


class TypeEPayroll(models.Model):
    _name = 'type.epayroll'
    _description = 'Type EPayroll'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    type = fields.Selection([('epayroll', 'Documento Soporte de Pago de Nómina Electrónica'), 
                            ('epayroll_ajus', 'Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica')], string='Tipo de XML')
    document_type = fields.Selection([('invoice', 'Invoices'),
                                        ('debit_note', 'Debit Notes'),
                                        ('credit_note', 'Credit Notes'),
                                        ('payslip', 'Nomina Individual'),
                                    ('payslip_ajuste', 'Nomina Individual De Ajuste')], string='Document Type')
    code_prefix_file = fields.Char('Document Code Prefix', help="Nombre del Archivo xml")
    sequence_id = fields.Many2one('ir.sequence', string='Secuencia nombre XML')

    

#