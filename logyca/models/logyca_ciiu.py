# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ciiu(models.Model):
    _name = 'logyca.ciiu'
    _parent_store = True
    _parent_name  = 'parent_id'
    _description = 'CIIU - Actividades economicas'

    code = fields.Char('Codigo', required=True)
    name = fields.Char('Name', required=True)
    porcent_ica = fields.Float(string='Porcentaje ICA')
    parent_id = fields.Many2one('logyca.ciiu','Parent Tag', ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('logyca.ciiu', 'parent_id', 'Child Tags')

    def name_get(self):
        return [(record.id, '%s' %
                 (record.name)) for record in self]
