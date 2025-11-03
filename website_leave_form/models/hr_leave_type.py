# -*- coding: utf-8 -*-
from odoo import fields, models

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    require_attachment = fields.Boolean(
        string='Requiere Adjuntos',
        default=False,
        help='Si está marcado, las solicitudes de este tipo deben incluir documentos adjuntos'
    )
    
    one_day_per_semester = fields.Boolean(
        string='Un día por semestre',
        default=False,
        help='Si está marcado, solo se permite un día de este tipo de ausencia por semestre'
    )
