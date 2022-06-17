from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)

#---------------------------Modelo Grupos Colaborativos-------------------------------#

class CollaborativeGroup(models.Model):
    _name = 'collaborative.group'

    name = fields.Char('Nombre')
    active = fields.Boolean('Activo')
