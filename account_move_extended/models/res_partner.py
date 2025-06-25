# -*- coding: utf-8 -*-


from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import formatLang
from odoo import api, fields, models, _

from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'


    macro_sector = fields.Selection([('manufactura', 'Manufactura'), 
                                    ('servicios', 'Servicios'),
                                    ('comercio', 'Comercio')], string='Macrosector')
    income_ids = fields.One2many('revenue.macro.sector.partner', 'partner_id', string='Ingresos')
    size_sector_int = fields.Selection([('micro1', 'Micro 1'),
                                        ('micro2', 'Micro 2'),
                                        ('micro3', 'Micro 3'), 
                                        ('pequena1', 'Pequeña 1'),
                                        ('pequena2', 'Pequeña 2'),
                                        ('pequena3', 'Pequeña 3'),
                                        ('mediana1', 'Mediana 1'),
                                        ('mediana2', 'Mediana 2'),
                                        ('mediana3', 'Mediana 3'),
                                        ('grande1', 'Grande 1'),
                                        ('grande2', 'Grande 2'),
                                        ('grande3', 'Grande 3'),
                                        ('grande4', 'Grande 4'),
                                    ('grande5', 'Grande 5')], string='Tamaño Empresa Interno')
    fact_annual = fields.Selection([('activos', 'Por Activos'), 
                                    ('ingresos', 'Por Ingresos')], string='Facturación Anual', default='activos', tracking=True)
    amount_revenue_membre = fields.Float('Ingresos Memebresía', default=0.0)
    revenue_memb_ids = fields.Many2one('revenue.macro.sector', string='Rango de Ingresos Membresía')
    x_income_range = fields.Many2one('revenue.macro.sector', string='Rango de ingresos', tracking=True, ondelete='restrict')


    def action_update_revenue_partner(self):
        view_id = self.env.ref('account_move_extended.update_revenue_wizard_wizard_view').id,
        return {
            'name':_("Actualizar Ingresos"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'update.revenue.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }


    def action_update_revenue_partner_membre(self):
        view_id = self.env.ref('account_move_extended.update_revenue_wizard_wizard_view_mb').id,
        return {
            'name':_("Actualizar Ingresos Membresía"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'update.revenue.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # The context key 'no_vat_validation' allows you to store/set a VAT number without doing validations.
        # This is for API pushes from external platforms where you have no control over VAT numbers.
        if self.env.context.get('no_vat_validation'):
            return
        if not self.env.context.get('no_vat_validation'):
            return

        for partner in self:
            country = partner.commercial_partner_id.country_id
            if partner.vat and self._run_vat_test(partner.vat, country, partner.is_company) is False:
                partner_label = _("partner [%s]", partner.name)
                msg = partner._build_vat_error_message(country and country.code.lower() or None, partner.vat, partner_label)
                raise ValidationError(msg)

    def write(self, values):
        print('WRITEEERR', values)
        # Si estamos actualizando la orden GS1, saltamos la comprobación de grupo
        if 'sale_gs1_id' in values:
            return super(ResPartner, self).write(values)        
        if 'second_gs1' in values:
            return super(ResPartner, self).write(values)        
        if 'date_second_gs1' in values:
            return super(ResPartner, self).write(values)        
        if not self.env.user.has_group('account_move_extended.account_move_manager_main_partner'):
            raise ValidationError(_('You are not authorized to change the company, please contact'))
        return super(ResPartner, self).write(values)
