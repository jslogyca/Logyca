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
                                        ('2', 'Refacturación')        
                                    ], string='Tipo de proceso', required=True)
    url_enpoint_code_assignment = fields.Char(string='Url enpoint de asignación', help='Url del endpoint del api de asignación dedicado a la facturación/refacturación masiva que recibe como parametro la lista de Nits y el tipo de proceso.',required=True)
    thirdparties = fields.Many2many('res.partner',string='Compañías catalogadas como miembros y clientes activos', readonly=True)    
    cant_thirdparties_miembros = fields.Integer(string='Cantidad de Miembros', readonly=True)
    cant_thirdparties_clientes = fields.Integer(string='Cantidad de Clientes', readonly=True)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "{}".format(record.name)))
        return result
    
    #Consultar Nits
    def consult_companies(self):  
        
        if self.process_type == '2':
            raise ValidationError(_('La lógica para refacturación está pendiente para ser desarrollada.'))             
        
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
        thirdparties = self.env['res.partner'].search([('x_active_vinculation', '=', True),('x_type_vinculation','in',types_vinculation)])
        #Cargar las compañias para mostrar en pantalla
        companies = []
        for company in thirdparties:
            companies.append(company.id)            
        
        #Traer la cantidad de miembros y clientes
        miembros = self.env['res.partner'].search([('x_active_vinculation', '=', True),('x_type_vinculation','in',[id_miembros])])
        cant_thirdparties_miembros = len(miembros)
        clientes = self.env['res.partner'].search([('x_active_vinculation', '=', True),('x_type_vinculation','in',[id_clientes])])
        cant_thirdparties_clientes = len(clientes)
        
        values_update = {
            'thirdparties' : [(6, 0, companies)],
            'cant_thirdparties_miembros' : cant_thirdparties_miembros, 
            'cant_thirdparties_clientes' : cant_thirdparties_clientes
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
			<newline/>
			<field name="url_enpoint_code_assignment" modifiers="{&quot;required&quot;: true}"/>
			<newline/>
			<button name="consult_companies" string="Consultar compañias" type="object" class="oe_highlight"/>
			<newline/>
			<field name="cant_thirdparties_miembros" modifiers="{&quot;readonly&quot;: true}"/>
			<field name="cant_thirdparties_clientes" modifiers="{&quot;readonly&quot;: true}"/>
			<newline/>
			<field name="thirdparties" colspan="4" can_create="true" can_write="true" modifiers="{&quot;readonly&quot;: true}"/>
			<newline/>
			<separator/>
		</group>
	</sheet>
</form>
'''