# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class FormSendDS(models.Model):
    _name = 'form.send.ds'
    _description = "Form Send DS"

    # 16.3.6 Códigos de descuento
    name = fields.Text('Name', required=True)
    code = fields.Char('Code', required=True)

    def name_get(self):
        return [(form.id, '%s - %s' %
                 (form.code, form.name)) for form in self]
