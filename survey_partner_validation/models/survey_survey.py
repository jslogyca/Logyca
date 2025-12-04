# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'
    
    form_partner = fields.Boolean('Formulario Terceros', default=False)
