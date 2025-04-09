# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError


class TypeTributos(models.Model):
    _name= 'type.tributos'
    _description = "TypeTributos"

    # 13.2.2. Tributos
    name = fields.Text('Name', required=True)
    code = fields.Char('Code', required=True)
    description = fields.Char('Description', required=True)
    active = fields.Boolean('Active', default=True)

    def name_get(self):
        return [(type.id, '%s - %s' % (type.code, type.name)) for type in self]
