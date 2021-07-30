# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError,ValidationError
from odoo.tools import float_is_zero, pycompat
from odoo.addons import decimal_precision as dp
from odoo.osv import expression
from datetime import date,datetime
import logging
_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"


    depart_parent_id = fields.Many2one('hr.department', 'Department', related='department_id.parent_id', readonly=True, store=True)
    x_document_type = fields.Selection([
                                        ('11', 'Registro civil de nacimiento'),
                                        ('12', 'Tarjeta de identidad'),
                                        ('13', 'Cédula de ciudadania'),
                                        ('21', 'Tarjeta de extranjería'),
                                        ('22', 'Cedula de extranjería'),
                                        ('31', 'NIT'),
                                        ('41', 'Pasaporte'),
                                        ('42', 'Tipo de documento extranjero'),
                                        ('43', 'Sin identificación del exterior o para uso definido por la DIAN'),
                                        ('44', 'Documento de identificación extranjero persona jurídica')
                                    ], string='Tipo de documento', track_visibility='onchange')


    # @api.onchange('department_id')
    # def _onchange_parent_id(self):
    #     print('asdfsdfdsfadf')
    #     erororor
    #     for employee in self:
    #         print('asdfsdfdsfadf  1111111')
    #         if employee.department_id:
    #             print('asdfsdfdsfadf 222222')
    #             employee.depart_parent_id = employee.department_id.parent_id


    # @api.depends('department_id')
    # def _compute_parent_id(self):
    #     if self.department_id:
    #         print('asdfsdfdsfadf 999999')
    #         employee.depart_parent_id = employee.department_id.parent_id
    #     return super(HrEmployeeBase, self)._compute_parent_id()