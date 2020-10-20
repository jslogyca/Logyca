# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import io
import requests
import json

#---------------------------------- Ejecucón del proceso - Facturación masiva
class x_MassiveInvoicingProcess(models.TransientModel):
    _name = 'massive.invoicing.process'
    _description = 'Massive Invoicing - Execute Process'
    
    year = fields.Integer(string='Año proceso', required=True)
    invoicing_companies = fields.Many2one('massive.invoicing.companies', string='Empresas a ejecutar', required=True)
    #Cantidad de prefijos
    cant_prefixes_ds = fields.Integer(string='Cantidad de códigos 4D a 7D', readonly=True) 
    cant_prefixes_mixed = fields.Integer(string='Cantidad de códigos mixtos', readonly=True) 
    cant_prefixes_gtin = fields.Integer(string='Cantidad de códigos GTIN8', readonly=True) 
    cant_prefixes_wrong = fields.Integer(string='Cantidad de códigos con inconsistencia (GLN, GL13, 8D)', readonly=True) 
    
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Facturación Masiva - {}".format(record.year)))
        return result
    
    #Tipos de vinculación valido (Miembro y cliente)
    def get_types_vinculation(self):
        types_vinculation = []
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        for m in obj_type_vinculation_miembros:
            types_vinculation.append(m.id)            
        for c in obj_type_vinculation_cliente:
            types_vinculation.append(c.id) 
        
        return types_vinculation
    
    #Consumir endpoint API de asignación de códigos
    def enpoint_code_assignment(self):
        #Tipo de proceso
        process_type = self.invoicing_companies.process_type
        if process_type == '1':
            process = False
        else:
            process = True
        #Obtener lista de Nits
        thirdparties = []
        for partner in self.invoicing_companies.thirdparties:            
            if partner.vat:
                thirdparties.append(partner.vat)
        #Ejecutar API de asignación de codigos
        body_api = json.dumps({'IsRefact': process, 'Nits': thirdparties})
        headers_api = {'content-type': 'application/json'}
        url_api = self.invoicing_companies.url_enpoint_code_assignment
        response = requests.get(url_api,data=body_api, headers=headers_api)
        
        return response.json()
    
    #Cálculo de cantidad de prefijos
    def calculation_of_number_prefixes(self):  
        invoicing_companies = self.enpoint_code_assignment()
        
        prefixes_ds = []
        cant_prefixes_ds = 0
        prefixes_gtin = []
        cant_prefixes_gtin = 0  
        prefixes_wrong = []
        cant_prefixes_wrong = 0
        
        for partner in invoicing_companies:
            partner_range = partner['Rango']
            
            if partner_range in ['4D','5D','6D','7D']:
                prefixes_ds.append(partner)
            if partner_range in ['GTIN8']:
                prefixes_gtin.append(partner)
            if partner_range in ['GLN','GL13','8D']:
                prefixes_wrong.append(partner)
        
        cant_prefixes_ds = len(prefixes_ds)
        cant_prefixes_gtin = len(prefixes_gtin)
        cant_prefixes_wrong = len(prefixes_wrong)
        
        self.cant_prefixes_ds = cant_prefixes_ds
        self.cant_prefixes_gtin = cant_prefixes_gtin
        self.cant_prefixes_wrong = cant_prefixes_wrong
