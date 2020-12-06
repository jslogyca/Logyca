# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

# Modelo para la identificación de empresas para Facturación/refacturación (masiva)
class x_MassiveInvoicingCompanies(models.Model):
    _name = 'massive.invoicing.companies'
    _description = 'Massive Invoicing - Companies for invoicing'
    
    name = fields.Char(string='Descripción', required=True)
    process_type = fields.Selection([
                                        ('1', 'Facturación'),
                                        ('2', 'Facturación Adicional'),                                        
                                    ], string='Tipo de proceso', required=True)
    textile_code_capability = fields.Float(string='Capacidad de códigos textiles', required=True)
    percentage_textile_tariff = fields.Integer(string='Porcentaje de la tarifa que aplica para facturar', required=True)
    url_enpoint_code_assignment = fields.Char(string='Url enpoint de asignación', help='Url del endpoint del api de asignación dedicado a la facturación/refacturación masiva que recibe como parametro la lista de Nits y el tipo de proceso.',required=True)    
    expiration_date = fields.Date(string='Fecha de vencimiento proceso',required=True)
    thirdparties = fields.Many2many('res.partner',string='Compañías catalogadas como miembros y clientes activos')    
    cant_thirdparties_miembros = fields.Integer(string='Cantidad de Miembros', help='Empresas que tiene tipo de vinculación Miembros',readonly=True)
    cant_thirdparties_clientes = fields.Integer(string='Cantidad de Clientes', help='Empresas que tiene tipo de vinculación Cliente',readonly=True)
    cant_thirdparties_textil = fields.Integer(string='Cantidad de Empresas Textileras', help='Empresas que tiene el Sector 10 - Textil y Confección',readonly=True)
    cant_thirdparties_gtin_special = fields.Integer(string='Cantidad de Empresas especiales GTIN8', help='Empresas especiales GTIN8 incluidas en facturación masiva',readonly=True)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "{}".format(record.name)))
        return result
    
    #Consultar Nits
    def consult_companies(self):  
        
        if self.process_type == '2':
            raise ValidationError(_('¡Por desarrollar!'))             
        
        #Consultar los tipos de vinculación Miembro y cliente
        id_miembros = 0
        id_clientes = 0
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        types_vinculation = []
        for m in obj_type_vinculation_miembros:
            types_vinculation.append(m.id)
            id_miembros = m.id
        for c in obj_type_vinculation_cliente:
            types_vinculation.append(c.id)  
            id_clientes = c.id
        #Crear objeto res_partner que traiga la información correspondiente - Compañías catalogadas como miembros y clientes activos
        thirdparties = self.env['res.partner'].search([('x_excluded_massive_invoicing','=',False),('x_active_vinculation', '=', True),('x_type_vinculation','in',types_vinculation)])
        #Cargar las compañias para mostrar en pantalla
        companies = []
        for company in thirdparties:
            companies.append(company.id)    
            
        #Empresas especiales GTIN8 incluidas en facturación masiva
        thirdparties_gtin = self.env['res.partner'].search([('x_gtin_massive_invoicing','=',True)])
        cant_thirdparties_gtin_special = len(thirdparties_gtin)
        for company_gtin in thirdparties_gtin:
            companies.append(company_gtin.id)  
        
        #Traer la cantidad de miembros, clientes y textileras
        miembros = self.env['res.partner'].search([('x_excluded_massive_invoicing','=',False),('x_active_vinculation', '=', True),('x_type_vinculation','in',[id_miembros])])
        cant_thirdparties_miembros = len(miembros)
        clientes = self.env['res.partner'].search([('x_excluded_massive_invoicing','=',False),('x_active_vinculation', '=', True),('x_type_vinculation','in',[id_clientes])])
        cant_thirdparties_clientes = len(clientes)
        textileras = self.env['res.partner'].search([('x_excluded_massive_invoicing','=',False),('x_active_vinculation', '=', True),('x_type_vinculation','in',types_vinculation),('x_sector_id.code','=','10')])
        cant_thirdparties_textil = len(textileras)
        
        values_update = {
            'thirdparties' : [(6, 0, companies)],
            'cant_thirdparties_miembros' : cant_thirdparties_miembros, 
            'cant_thirdparties_clientes' : cant_thirdparties_clientes,
            'cant_thirdparties_textil' : cant_thirdparties_textil,
            'cant_thirdparties_gtin_special' : cant_thirdparties_gtin_special
        }
        self.update(values_update)     
        
        
               
# XML Vista / Comentario
'''
<form>
	<sheet string="Massive Invoicing - Companies for invoicing">
		<group col="4">
			<field name="name" modifiers="{&quot;required&quot;: true}"/>
			<newline/>
			<field name="process_type" modifiers="{'required': true}" widget="radio"/>
			<field name="expiration_date" modifiers="{&quot;required&quot;: true}"/>
			<newline/>
			<field name="url_enpoint_code_assignment" modifiers="{&quot;required&quot;: true}"/>
			<newline/>
			<b>Parametros empresas textileras</b>
			<div style="padding:5px;border:solid;">                        
  			Capacidad de códigos: <field name="textile_code_capability" modifiers="{&quot;required&quot;: true}"/>
  			<br/>
  			Porcentaje de la tarifa: <field name="percentage_textile_tariff" modifiers="{&quot;required&quot;: true}"/>
  		</div>
			<newline/>
			<button name="consult_companies" string="Consultar compañias" type="object" class="oe_highlight" style="margin:5px;" attrs="{'invisible': [('process_type', '=', '2')]}"/>
			<newline/>
			<field name="cant_thirdparties_miembros" modifiers="{&quot;readonly&quot;: true}" attrs="{'invisible': [('process_type', '=', '2')]}"/>
			<field name="cant_thirdparties_clientes" modifiers="{&quot;readonly&quot;: true}" attrs="{'invisible': [('process_type', '=', '2')]}"/>
			<field name="cant_thirdparties_textil" modifiers="{&quot;readonly&quot;: true}" attrs="{'invisible': [('process_type', '=', '2')]}"/>
			<field name="cant_thirdparties_gtin_special" modifiers="{&quot;readonly&quot;: true}" attrs="{'invisible': [('process_type', '=', '2')]}"/>
			<newline/>
			<field name="thirdparties" colspan="4" can_create="true" can_write="true" attrs="{'readonly': [('process_type', '=', '1')]}">
          <tree>
              <field name="name"/>
              <field name="vat"/>     
              <field name="x_date_vinculation"/>                                        
              <field name="x_type_vinculation" widget="many2many_tags"/>                                        
              <field name="x_sector_id"/>                                        
          </tree>
      </field>
			<newline/>
			<separator/>
		</group>
	</sheet>
</form>
'''