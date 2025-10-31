# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'
    
    def action_associate_partner_by_nit(self):
        """
        Busca el tercero por NIT (almacenado en nickname) y asocia la encuesta
        """
        for record in self:
            if not record.nickname:
                raise UserError(_('No se encontró el NIT en el campo Apodo (nickname).'))
            
            # Buscar el tercero por VAT (NIT)
            partner = self.env['res.partner'].search([
                ('vat', '=', record.nickname),
                ('parent_id', '=', None)
            ], limit=1)
            
            if not partner:
                raise UserError(_(
                    'No se encontró ningún tercero con NIT: %s\n'
                    'Por favor, verifique que el tercero esté creado en el sistema.'
                ) % record.nickname)
            
            # Asociar el tercero a la respuesta de encuesta
            record.write({'partner_id': partner.id})
            
            # También actualizar el partner_id en el modelo survey.user_input si existe
            if hasattr(record, 'partner_id'):
                record.partner_id = partner.id
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Éxito'),
                    'message': _('Tercero %s asociado correctamente a la encuesta.') % partner.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
    
    @api.model
    def create(self, vals):
        """
        Al crear una respuesta, intentar asociar automáticamente el tercero si existe el NIT
        """
        res = super(SurveyUserInput, self).create(vals)
        
        # Si tiene nickname (NIT), intentar asociar automáticamente
        if res.nickname:
            try:
                partner = self.env['res.partner'].search([
                    ('vat', '=', res.nickname)
                ], limit=1)
                if partner:
                    res.partner_id = partner.id
            except:
                # Si hay error, continuar sin asociar
                pass
        
        return res
