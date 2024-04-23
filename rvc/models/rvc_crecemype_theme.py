from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class rvc_crecemype_theme(models.Model):
    _name = 'rvc.crecemype.theme'

    _description = """
        Temáticas que pueden consultar las empresas en el beneficio
        Crece Mype del programa RVC de LOGYCA
    """

    name = fields.Char('Nombre')
    active = fields.Boolean('Activo')