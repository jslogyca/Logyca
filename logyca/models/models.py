# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

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

    code = fields.Char(string='Identificador', size=5, required=True)
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

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{}".format(record.name)))
        return result

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
	
    x_automatic_activation = fields.Boolean(string='Activación automática')
    x_code_type = fields.Integer(string='Tipo de codigo')
    x_mandatory_prefix = fields.Integer(string='Prefijo obligatorio') 
    x_scheme = fields.Integer(string='Esquema')
    x_type_document = fields.Integer(string='Tipo documento')
    x_date_validity = fields.Datetime(string='Fecha de expiración')

class SaleOrder(models.Model):
    _inherit = 'sale.order'
	
    x_origen = fields.Char(string='Origen',size=30)
    
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
                return super(PurchaseOrder, self).button_cancel()
            else:
                raise UserError(_("Debe llenar el campo motivo de cancelación antes de cancelar."))
    
    #Validaciones antes de CONFIRMAR una orden de compra
    def button_confirm(self):
        for order_line in self.order_line:
            if (order_line.account_analytic_id == False) and (order_line._onchange_analytic_tag_ids == False):
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

    
    