# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        """
        Valida que el tercero tenga la encuesta completada antes de publicar la factura
        """
        for move in self:
            # Solo validar facturas de cliente (out_invoice y out_refund)
            if move.move_type in ['out_invoice', 'out_refund'] and move.partner_id:
                partner = move.partner_id
                
                # Verificar si el tercero requiere encuesta
                if partner.requires_survey:
                    # Verificar si tiene la encuesta completada
                    if not partner.survey_completed:
                        raise UserError(_(
                            'No se puede publicar la factura.\n\n'
                            'El tercero "%s" (NIT: %s) fue creado después del 31 de octubre de 2025 '
                            'y debe completar la encuesta requerida antes de poder facturar.\n\n'
                            'Por favor, asegúrese de que el tercero complete la encuesta.'
                        ) % (partner.name, partner.vat or 'Sin NIT'))
        
        return super(AccountMove, self).action_post()

    @api.constrains('state', 'partner_id')
    def _check_partner_survey_on_post(self):
        """
        Constraint adicional para asegurar la validación
        """
        for move in self:
            if move.state == 'posted' and move.move_type in ['out_invoice', 'out_refund']:
                if move.partner_id and move.partner_id.requires_survey:
                    if not move.partner_id.survey_completed:
                        raise ValidationError(_(
                            'El tercero %s requiere tener una encuesta completada '
                            'para poder publicar facturas.'
                        ) % move.partner_id.name)
