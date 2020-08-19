# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging
import datetime
_logger = logging.getLogger(__name__)
#--------------------------------Modelos propios de logyca------------------------------------#

# CIUDAD
class x_city(models.Model):
    _name = 'logyca.city'
    _description = 'Ciudades por departamento'

    state_id = fields.Many2one('res.country.state', string='Departamento', required=True)
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

# CIIU
class ciiu(models.Model):
    _name = 'logyca.ciiu'
    _parent_store = True
    _parent_name  = 'parent_id'
    _description = 'CIIU - Actividades economicas'

    code = fields.Char('Codigo', required=True)
    name = fields.Char('Name', required=True)
    porcent_ica = fields.Float(string='Porcentaje ICA')
    parent_id = fields.Many2one('logyca.ciiu','Parent Tag', ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('logyca.ciiu', 'parent_id', 'Child Tags')    
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

# SECTORES
class x_sectors(models.Model):
    _name = 'logyca.sectors'
    _description = 'Sectores'

    code = fields.Char(string='Código', size=10,required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# TIPOS DE VINCULACION
class x_vinculation_types(models.Model):
    _name = 'logyca.vinculation_types'
    _description = 'Tipos de vinculación'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', size=100, required=True)
    active = fields.Boolean(string='Activo')
    novelty = fields.Selection([('1', 'Vigente'), ('2', 'No esta vigente para nuevos - se mantiene para las empresas que lo adquirieron')], string='Novedad', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# RESPONSABILIDADES RUT
class x_responsibilities_rut(models.Model):
    _name = 'logyca.responsibilities_rut'
    _description = 'Responsabilidades RUT'

    code = fields.Char(string='Identificador', size=10, required=True)
    description = fields.Char(string='Descripción', size=100, required=True)
    valid_for_fe = fields.Boolean(string='Valido para facturación electrónica')
    
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.description)))
        return result

# TIPOS DE CONTACTO
class x_contact_types(models.Model):
    _name = 'logyca.contact_types'
    _description = 'Tipos de contacto'
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# ÁREAS
class x_areas(models.Model):
    _name = 'logyca.areas'
    _description = 'Áreas'
    _order = 'code,name'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# CARGOS
class x_job_title(models.Model):
    _name = 'logyca.job_title'
    _description = 'Cargos'
    _order = 'area_id,code,name'

    area_id = fields.Many2one('logyca.areas', string='Área')
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# GRUPOS DE TRABAJO
class x_work_groups(models.Model):
    _name = 'logyca.work_groups'
    _description = 'Grupos de Trabajo'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} | {}".format(record.code, record.name)))
        return result

# TIPOS DE TERCERO
class x_type_thirdparty(models.Model):
    _name = 'logyca.type_thirdparty'
    _description = 'Tipos de tercero'
    
    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    types = fields.Selection([('1', 'Cliente / Cuenta'),
                              ('2', 'Contacto'),
                              ('3', 'Proveedor'),
                              ('4', 'Funcionario / Contratista')], string='Tipo', required=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

# Racngos de activos
class x_asset_range(models.Model):
    _name = 'logyca.asset_range'
    _description = 'Rangos de activos'
    
    initial_value = fields.Float(string='Valor inicial', required=True)
    final_value = fields.Float(string='Valor final', required=True)
    name = fields.Char(string='Nombre', required=True)
    active = fields.Boolean(string='Activo')
    assigned_codes = fields.Integer(string='Nro. Asignación de codigos')

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

# Grupo Presupuestal
class x_budget_group(models.Model):
    _name = 'logyca.budget_group'
    _description = 'Grupos presupuestal'

    code = fields.Char(string='Código', size=10, required=True)
    name = fields.Char(string='Nombre', required=True)
    lser_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Servicios', domain="[('company_id', '=', 1)]")
    iac_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Asociación', domain="[('company_id', '=', 2)]")
    log_analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica Logyca Investigación', domain="[('company_id', '=', 3)]")
     
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

class x_api_gateway(models.Model):
    _name = 'logyca.api_gateway'
    _description = 'Movimientos API'

    method = fields.Char(string='Método', required=True)
    send_date = fields.Char(string='Fecha envió', compute='_send_date', store=True,required=True)    
    send_json = fields.Text(string='Json')    
    x_return = fields.Text(string='Respuesta')
    cant_attempts = fields.Integer(string='Cantidad de intentos')
    
    @api.depends('method')
    def _send_date(self):
        send_date = fields.Datetime.context_timestamp(self, timestamp=datetime.datetime.now())
        self.send_date = str(send_date)
    
#--------------------------------Modelos heredados de Odoo------------------------------------#

class ResCountry(models.Model):
    _inherit = 'res.country'
	
    x_code_dian = fields.Char(string='Código del país para la DIAN')

class ResCountryState(models.Model):
    _inherit = 'res.country.state'
	
    x_code_dian = fields.Char(string='Código de provincia/departamento para la DIAN')

class CRMTeam(models.Model):
    _inherit = 'crm.team'
	
    invoiced_target = fields.Float('Meta de Facturación',(12,0))

class ProductTemplate(models.Model):
    _inherit = 'product.template'
	
    x_is_deferred = fields.Boolean(string='¿Es Diferido?',track_visibility='onchange')
    x_automatic_activation = fields.Boolean(string='Activación automática',track_visibility='onchange')
    x_code_type = fields.Integer(string='Tipo de codigo',track_visibility='onchange')
    x_mandatory_prefix = fields.Integer(string='Prefijo obligatorio',track_visibility='onchange') 
    x_scheme = fields.Integer(string='Esquema',track_visibility='onchange')
    x_type_document = fields.Integer(string='Tipo documento',track_visibility='onchange')
    x_date_validity = fields.Datetime(string='Fecha de expiración',track_visibility='onchange')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
	
    x_origen = fields.Char(string='Origen',size=30)
    x_vat_partner = fields.Char(string='NIT Asociado', store=True, readonly=True, related='partner_id.vat', change_default=True)
    x_type_sale = fields.Selection([('Renovación', 'Renovación'),
                                      #('Recurrente', 'Recurrente'),
                                      ('Nueva venta', 'Nueva venta')], string='Tipo de venta') 
    
    def _prepare_invoice(self):        
        invoice_vals = super(SaleOrder, self)._prepare_invoice()        
        self.ensure_one()
        self = self.with_context(default_company_id=self.company_id.id, force_company=self.company_id.id)        
        country_id = self.partner_invoice_id.country_id.id        
        invoice_vals['x_country_account_id'] = country_id        
        return invoice_vals
    
    #Validaciones antes de CONFIRMAR una orden de venta
    #def action_confirm(self):
    #    for order_line in self.order_line:
    #        if order_line.account_analytic_id == False:
    #            raise UserError(_("No se digito información analítica (Cuenta o Etiqueta) para el registro "+order_line.name+", por favor verificar."))
    #    return super(SaleOrder, self).action_confirm()  
    
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

    
class HelpDesk(models.Model):
    _inherit = 'helpdesk.ticket'
	
    x_origen = fields.Char(string='Origen',size=50)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
	
    x_reason_cancellation = fields.Text(string='Motivo de cancelación')
    
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
            if not order_line.x_budget_group:
                raise UserError(_("No se digito información el grupo presupuestal para el registro "+order_line.name+", por favor verificar."))
                
            if not order_line.account_analytic_id and not order_line.analytic_tag_ids:
                raise UserError(_("No se digito información analítica (Cuenta o Etiqueta) para el registro "+order_line.name+", por favor verificar."))
            
        return super(PurchaseOrder, self).button_confirm()            
           
    
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    #Grupo de trabajo 
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal')
    
    #Cuenta analitica 
    @api.onchange('account_analytic_id')    
    def _onchange_analytic_account_id(self):
        if self.account_analytic_id:
            self.analytic_tag_ids = [(5,0,0)]
            
    #Etiqueta analitica
    @api.onchange('analytic_tag_ids')
    def _onchange_analytic_tag_ids(self):
        if self.analytic_tag_ids:
            self.account_analytic_id = False

    
    