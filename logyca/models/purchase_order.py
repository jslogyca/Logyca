# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
	
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
    
    x_reason_cancellation = fields.Text(string='Motivo de cancelación')
    x_country_account_id = fields.Many2one('res.country', string='País', default=_get_default_country_id, tracking=True)
    x_studio_listo_para_facturar = fields.Boolean(string='Listo para Facturar', default=False)

    #Validaciones antes de CANCELAR una orden de compra
    def button_cancel(self):        
        for record in self:
            if record.x_reason_cancellation:
                
                #Envio correo
                emails = list(set([record.create_uid.email]))
                
                subject = _("Cancelación orden de compra %s" % record.name)
                body = _("""La orden de compra (%s) fue cancelada:
                              - Motivo cancelación: %s 
                            
                            Datos de la orden de compra:
                              - Proveedor: %s
                              - Fecha pedido: %s
                              - Referencia: %s"""
                         % (record.name, record.x_reason_cancellation, record.partner_id.name, record.date_order, record.partner_ref))
                    
                email = self.env['ir.mail_server'].build_email(
                        email_from=self.env.user.email,
                        email_to=emails,
                        subject=subject, 
                        body=body,
                )
                
                self.env['ir.mail_server'].send_email(email)
                
                # Ejecutar metodo inicial
                super(PurchaseOrder, self).button_cancel()
                
            else:
                raise UserError(_("Debe llenar el campo motivo de cancelación antes de cancelar."))
    
    #Validaciones antes de CONFIRMAR una orden de compra
    def button_confirm(self):
        for order_line in self.order_line:
            if order_line.analytic_distribution and not order_line.x_budget_group:
                budget_group = self.env['logyca.budget_group'].search([('by_default_group', '=', True), 
                                        ('company_id', '=', order_line.company_id.id)], order="id asc", limit=1)
                if budget_group:
                    order_line.x_budget_group = budget_group
            
            if not order_line.x_budget_group:
                raise UserError(_("No se digito información el grupo presupuestal para el registro "+order_line.name+", por favor verificar."))

            if order_line.analytic_distribution:
                total = sum(order_line.analytic_distribution.values())
                if total > 100:
                    raise ValidationError(
                        f"La distribución analítica en la línea con producto '{order_line.product_id.display_name}' supera el 100% (actual: {total:.2f}%)."
                    )
                
            # if not order_line.account_analytic_id and not order_line.analytic_tag_ids:
            #     raise UserError(_("No se digito información analítica (Cuenta o Etiqueta) para el registro "+order_line.name+", por favor verificar."))
            
        return super(PurchaseOrder, self).button_confirm()
