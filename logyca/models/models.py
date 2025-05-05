# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import datetime

from random import randint

_logger = logging.getLogger(__name__)
#--------------------------------Modelos propios de logyca------------------------------------#
    
#--------------------------------Modelos heredados de Odoo------------------------------------#

class CRMTeam(models.Model):
    _inherit = 'crm.team'
	
    invoiced_target = fields.Float('Meta de Facturación',(12,0))

class ProductTemplate(models.Model):
    _inherit = 'product.template'
	
    x_is_deferred = fields.Boolean(string='¿Es Diferido?',tracking=True)
    x_automatic_activation = fields.Boolean(string='Activación automática',tracking=True)
    x_code_type = fields.Integer(string='Tipo de codigo',tracking=True)
    x_mandatory_prefix = fields.Integer(string='Prefijo obligatorio',tracking=True) 
    x_scheme = fields.Integer(string='Esquema',tracking=True)
    x_type_document = fields.Integer(string='Tipo documento',tracking=True)
    x_date_validity = fields.Datetime(string='Fecha de expiración',tracking=True)
    type_accountant = fields.Selection([
        ('costo', 'Costo'),
        ('gasto', 'Gasto'),
        ('gastov', 'Gasto Comercial'),
        ('na', 'No Aplica'),
    ], string='Tipo Contable', copy=False, default='na')    
    
class HelpDesk(models.Model):
    _inherit = 'helpdesk.ticket'
	
    x_origen = fields.Char(string='Origen',size=50)
