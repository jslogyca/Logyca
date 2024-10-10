# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class UpdateRevenueWizard(models.TransientModel):
    _name = "update.revenue.wizard"
    _description = "Income Macro Sector"

    amount = fields.Char('Ingresos')
    fiscal_id = fields.Many2one('account.fiscal.year', string='Ejercicio fiscal')

    def update_revenue_partner(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        obj_hr_partner = self.env['res.partner']
        rec_hr_partner = obj_hr_partner.browse(active_id)
        print('CONTACTO', rec_hr_partner)
        for partner in rec_hr_partner:
            if not partner.macro_sector:
                raise ValidationError(_('Debe ingresar el macrosector'))
            
            self._cr.execute(''' select id from revenue_macro_sector where %s between amount_start and amount_end 
                                    and macro_sector=%s ''', (self.amount, partner.macro_sector))
            renueve_obj = self._cr.fetchone()
            if renueve_obj and renueve_obj[0]:
                print('rango', renueve_obj, self.amount, partner.macro_sector)
                ems_id = self.env['revenue.macro.sector'].search([('id','=',renueve_obj[0])],limit=1)
                obj_mr= self.env['revenue.macro.sector.partner']
                details = {
                    'fiscal_id': self.fiscal_id.id,
                    'partner_id': partner.id,
                    'macro_sector': partner.macro_sector,
                    'revenue_ids': ems_id.id,
                    'amount': self.amount,
                }
                mr_id = obj_mr.create(details)
                partner.write({'size_sector_int': ems_id.size_sector_int, 'x_company_size':ems_id.x_company_size})
        return {'type': 'ir.actions.act_window_close'}


    def update_revenue_partner_mb(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        active_id = context.get('active_ids', False)
        obj_hr_partner = self.env['res.partner']
        rec_hr_partner = obj_hr_partner.browse(active_id)
        for partner in rec_hr_partner:
            if not partner.macro_sector:
                raise ValidationError(_('Debe ingresar el macrosector'))
            
            self._cr.execute(''' select id from revenue_macro_sector where %s between amount_start and amount_end 
                                    and macro_sector=%s ''', (self.amount, partner.macro_sector))
            renueve_obj = self._cr.fetchone()
            if renueve_obj and renueve_obj[0]:
                print('rango', renueve_obj, self.amount, partner.macro_sector)
                ems_id = self.env['revenue.macro.sector'].search([('id','=',renueve_obj[0])],limit=1)
                partner.write({'amount_revenue_membre': self.amount, 'revenue_memb_ids':ems_id.id})
        return {'type': 'ir.actions.act_window_close'}
