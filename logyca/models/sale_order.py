# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'
	
    @api.model
    def _get_default_country_id(self):
        country_id = 49
        
        if self.partner_id:
            partner = self.env['res.partner'].browse(self.partner_id.id)
            country_id = partner.country_id
        
        values = {
                'x_country_account_id': country_id ,                
            }
        self.update(values)
        
        return country_id
    
    x_origen = fields.Char(string='Origen',size=30)
    x_vat_partner = fields.Char(string='NIT Asociado', store=True, readonly=True, related='partner_id.vat', change_default=True)
    x_type_sale = fields.Selection([('Renovación', 'Renovación'),
                                      #('Recurrente', 'Recurrente'),
                                      ('Nueva venta', 'Nueva venta')], string='Tipo de venta') 
    x_country_account_id = fields.Many2one('res.country', string='País', default=_get_default_country_id, tracking=True)
    x_conditional_discount = fields.Float(string='Descuento condicionado')
    x_conditional_discount_deadline = fields.Date(string='Fecha límite descuento condicionado')    
    x_amount_total_conditional_discount = fields.Float(string='Total con descuento condicionado',compute='_compute_amount_total_conditional_discount')
    
    @api.depends('amount_total','x_conditional_discount')
    def _compute_amount_total_conditional_discount(self):
        amount_total_conditional_discount = 0
        for record in self:
            amount_total = record.amount_total
            conditional_discount = record.x_conditional_discount
            amount_total_conditional_discount = amount_total-conditional_discount
            record.x_amount_total_conditional_discount = amount_total_conditional_discount
    
    def _prepare_invoice(self):        
        invoice_vals = super(SaleOrder, self)._prepare_invoice()        
        self.ensure_one()
        self = self.with_context(default_company_id=self.company_id.id, force_company=self.company_id.id)        
        country_id = 0
        if self.x_country_account_id:
            country_id = self.x_country_account_id.id
        else:
            country_id = self.partner_invoice_id.country_id.id        
            
        invoice_vals['x_country_account_id'] = country_id        
        return invoice_vals

    #Validaciones antes de CONFIRMAR una orden de compra
    def action_confirm(self):
        for order_line in self.order_line:
            if not order_line.analytic_distribution:
                raise UserError(_("No se digito información la Analítica para el registro "+order_line.name+", por favor verificar."))

            if order_line.analytic_distribution:
                total = sum(order_line.analytic_distribution.values())
                if total > 100:
                    raise ValidationError(
                        f"La distribución analítica en la línea con producto '{order_line.product_id.display_name}' supera el 100% (actual: {total:.2f}%)."
                    )            
        return super(SaleOrder, self).action_confirm()        
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal')
    
class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    
    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)  
        country_id = order.partner_invoice_id.country_id.id        
        invoice_vals['x_country_account_id'] = country_id        
        
        return invoice_vals
