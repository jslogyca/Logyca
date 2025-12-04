# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    survey_completed = fields.Boolean(
        string='Encuesta Completada',
        compute='_compute_survey_completed',
        store=True,
        help='Indica si el tercero ha completado la encuesta requerida'
    )
    
    survey_input_count = fields.Integer(
        string='Número de Encuestas',
        compute='_compute_survey_input_count'
    )
    
    requires_survey = fields.Boolean(
        string='Requiere Encuesta',
        compute='_compute_requires_survey',
        store=True,
        help='Indica si el tercero fue creado después del 31/10/2025 y requiere encuesta'
    )

    @api.depends('create_date')
    def _compute_requires_survey(self):
        """
        Determina si el tercero requiere encuesta (creado después del 31/10/2025)
        """
        cutoff_date = datetime(2025, 10, 31, 23, 59, 59)
        
        for partner in self:
            if partner.create_date:
                partner.requires_survey = partner.create_date > cutoff_date
            else:
                partner.requires_survey = False

    @api.depends('survey_inputs', 'survey_inputs.state')
    def _compute_survey_completed(self):
        """
        Verifica si el tercero tiene al menos una encuesta completada
        """
        for partner in self:
            completed_surveys = partner.survey_inputs.filtered(lambda s: s.state == 'done' and s.survey_id.form_partner)
            partner.survey_completed = bool(completed_surveys)

    @api.depends('survey_inputs')
    def _compute_survey_input_count(self):
        """
        Cuenta el número de encuestas asociadas al tercero
        """
        for partner in self:
            partner.survey_input_count = len(partner.survey_inputs)

    def action_view_surveys(self):
        """
        Acción para ver las encuestas del tercero
        """
        self.ensure_one()
        return {
            'name': _('Encuestas de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def check_survey_requirement(self):
        """
        Verifica si el tercero cumple con el requisito de encuesta
        Retorna True si no requiere encuesta o si la tiene completada
        """
        self.ensure_one()
        
        # Si no requiere encuesta, retorna True
        if not self.requires_survey:
            return True
        
        # Si requiere encuesta, debe tenerla completada
        return self.survey_completed
