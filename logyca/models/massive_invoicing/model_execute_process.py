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
    #Respuesta API
    x_enpoint_code_assignment = fields.One2many('massive.invoicing.enpointcodeassignment', 'process_id', string = 'Respuesta API - Aginación de códigos', readonly=True)
    #Cantidad de prefijos
    x_partner_calculation_prefixes = fields.One2many('massive.invoicing.partnercalculationprefixes', 'process_id', string = 'Cálculo de cantidad de prefijos', readonly=True)
    #Ordenes de venta
    x_partner_sale_order = fields.One2many('massive.invoicing.partner.saleorder', 'process_id', string = 'Ordenes de venta', readonly=True)
        
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Facturación Masiva - {}".format(record.year)))
        return result
    
    #Consumir endpoint API de asignación de códigos
    def enpoint_code_assignment(self):
        #Tipo de proceso
        #process_type = self.invoicing_companies.process_type
        #if process_type == '1':
        #    process = False
        #else:
        #    process = True
        #Obtener lista de Nits
        thirdparties = []
        for partner in self.invoicing_companies.thirdparties:            
            if partner.vat:
                thirdparties.append(partner.vat)
        #Ejecutar API de asignación de codigos
        process = False
        body_api = json.dumps({'IsRefact': process, 'Nits': thirdparties})
        headers_api = {'content-type': 'application/json'}
        url_api = self.invoicing_companies.url_enpoint_code_assignment
        response = requests.get(url_api,data=body_api, headers=headers_api)
        
        #Eliminar llamado si ya existe
        enpointcodeassignment_exists = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', self.id)])
        enpointcodeassignment_exists.unlink()
        
        for data in response.json():
            partner_vat = data['Nit']
            enpointcodeassignment_vals = data
            enpointcodeassignment_vals['process_id'] = self.id
            
            for partner in self.invoicing_companies.thirdparties:
                if partner.vat == partner_vat:
                    partner_id = partner.id
                    enpointcodeassignment_vals['partner_id'] = partner_id                    
             
            #raise ValidationError(_(enpointcodeassignment_vals)) 
            enpointcodeassignment = self.env['massive.invoicing.enpointcodeassignment'].create(enpointcodeassignment_vals)
            
        return response.json()
    
    #Cálculo de cantidad de prefijos
    def calculation_of_number_prefixes(self):  
        
        #Eliminar llamado si ya existe
        partnercalculationprefixes_exists = self.env['massive.invoicing.partnercalculationprefixes'].search([('process_id', '=', self.id)])
        partnercalculationprefixes_exists.unlink()
        
        for partner in self.invoicing_companies.thirdparties:
            prefixes_ds = []
            cant_prefixes_ds = 0
            prefixes_fixed_weight = []
            cant_prefixes_fixed_weight = 0
            prefixes_variable_weight = []
            cant_prefixes_variable_weight = 0
            prefixes_mixed = []
            cant_prefixes_mixed = 0
            prefixes_gtin = []
            cant_prefixes_gtin = 0  
            prefixes_gl = []
            cant_prefixes_gl = 0
            prefixes_delete_fixes = []
            prefixes_delete_variable = []
            total_capacity_prefixes = []
            enpointcodeassignment = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', self.id),('partner_id','=',partner.id)])
            
            for data in enpointcodeassignment:            
                partner_vat = data.Nit
                partner_range = data.Rango
                total_capacity_prefixes.append({'Rango':partner_range,'Capacity':data.CapacidadPrefijo})
                                
                if partner_range in ['4D','5D','6D','7D','8D']:
                    prefixes_ds.append(data.PrefixId)
                if partner_range in ['PesoFijo']:
                    prefixes_fixed_weight.append(data.PrefixId)
                if partner_range in ['Peso variable']:
                    prefixes_variable_weight.append(data.PrefixId)
                if partner_range in ['GTIN8']:
                    prefixes_gtin.append(data.PrefixId)
                if partner_range in ['GLN','GL13']:
                    prefixes_gl.append(data.PrefixId)
            
            #Calculo prefijos mixtos
            for variable_weight in prefixes_variable_weight:
                if variable_weight[:2] == '29':
                    for fixed_weight in prefixes_fixed_weight:
                        if fixed_weight[:3] == '770' or fixed_weight[:3] == '771':
                            if variable_weight[-3:] == fixed_weight[-3:]:                                
                                #Se agrega en prefijos mixtos
                                prefixes_mixed.append(variable_weight+"|"+fixed_weight)
                                #Se eliminan de peso variable y peso fijo
                                prefixes_delete_fixes.append(fixed_weight)
                                prefixes_delete_variable.append(variable_weight)
            
            #Eliminar prefijos segun calculo de mixtos
            for delete_f in prefixes_delete_fixes:
                prefixes_fixed_weight.remove(delete_f)
            for delete_v in prefixes_delete_variable:
                prefixes_variable_weight.remove(delete_v)
            
            #Conteo
            cant_prefixes_ds = len(prefixes_ds)
            cant_prefixes_fixed_weight = len(prefixes_fixed_weight)
            cant_prefixes_variable_weight = len(prefixes_variable_weight)
            cant_prefixes_mixed = len(prefixes_mixed)
            cant_prefixes_gtin = len(prefixes_gtin)
            cant_prefixes_gl = len(prefixes_gl)
            
            if cant_prefixes_ds+cant_prefixes_fixed_weight+cant_prefixes_variable_weight+cant_prefixes_mixed+cant_prefixes_gtin+cant_prefixes_gl > 0:
                have_prefixes = '1'
            else:
                have_prefixes = '2'
            
            partnercalculationprefixes_values = {
                'process_id': self.id,
                'partner_id': partner.id,
                'vat': partner.vat,
                'have_prefixes': have_prefixes,
                'cant_prefixes_ds': cant_prefixes_ds,
                'prefixes_ds': str(prefixes_ds),
                'cant_prefixes_fixed_weight': cant_prefixes_fixed_weight,
                'prefixes_fixed_weight': prefixes_fixed_weight,
                'cant_prefixes_variable_weight': cant_prefixes_variable_weight,
                'prefixes_variable_weight': prefixes_variable_weight,
                'cant_prefixes_mixed': cant_prefixes_mixed,
                'prefixes_mixed': prefixes_mixed,                
                'cant_prefixes_gtin': cant_prefixes_gtin,
                'prefixes_gtin': prefixes_gtin,                
                'cant_prefixes_gl': cant_prefixes_gl,
                'prefixes_gl': prefixes_gl,
                'total_capacity_prefixes': total_capacity_prefixes,
            }
            
            partnercalculationprefixes = self.env['massive.invoicing.partnercalculationprefixes'].create(partnercalculationprefixes_values)
        
    #Ejecución proceso
    def execute_process(self): 
        #Eliminar ordenes de venta si ya existen solamente cuando se ejecute facturación masiva general y no adicional
        if self.invoicing_companies.process_type == '1':
            saleorder_exists = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year))])
            saleorder_exists.unlink()
        process_partnersaleorder_exists = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id)])
        process_partnersaleorder_exists.unlink()
        #Tipos de vinculación Miembro y CLiente
        type_vinculation_miembro = 0
        type_vinculation_cliente = 0
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        for m in obj_type_vinculation_miembros:
            type_vinculation_miembro = m.id
        for c in obj_type_vinculation_cliente:
            type_vinculation_cliente = c.id
        #Traer el sector de textileros
        sector_id_textil = 10 #Id definido, en caso de camviar revisar la tabla de sectores de Logyca
        #Traer los productos y sus tipos de proceso
        saler_orders_partner = []
        cant_prefixes_textil_partner = []
        obj_massive_invoicing_products = self.env['massive.invoicing.products'].search([('product_id', '!=', False)])
        for process in obj_massive_invoicing_products:
            type_vinculation = process.type_vinculation.id
            type_process = process.type_process
            product_id = process.product_id.id
            
            obj_company = self.env['massive.invoicing.partnercalculationprefixes'].search([('process_id', '=', self.id),('type_vinculation','in',[type_vinculation]),('have_prefixes','=','1')])
            #('partner_id.x_sector_id.id','!=',sector_id_textil),
            #,('partner_id.vat','in',['860000452','890901672','800197463','900677748','860025900'])
            for partner in obj_company:
                fee_value = 0
                unit_fee_value = 0
                discount = 0                       
                conditional_discount = 0
                conditional_discount_deadline = False
                        
                obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                for tariff in obj_tariff:
                    fee_value = tariff.fee_value
                    unit_fee_value = tariff.unit_fee_value
                    obj_tariff_discounts = self.env['massive.invoicing.tariff.discounts'].search([('tariff', '=', tariff.id)])
                    for tariff_discounts in obj_tariff_discounts:
                        #Logica descuento no condicionado
                        if tariff_discounts.discount_percentage > 0:
                            discount = tariff_discounts.discount_percentage
                        #Logica descuento condicionado
                        if tariff_discounts.discounts_one > 0:
                            conditional_discount = tariff_discounts.discounts_one 
                            conditional_discount_deadline = tariff_discounts.date_discounts_one 
                        
                #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                id_contactP = 0
                for record in partner.partner_id.child_ids:   
                    ls_contacts = record.x_contact_type
                    for i in ls_contacts:
                        if i.id == 2:
                            id_contactP = record.id
                    
                if id_contactP == 0:
                    id_contactP = partner.partner_id.id
                    
                #Clientes / Miembros.
                if type_vinculation == type_vinculation_miembro or type_vinculation == type_vinculation_cliente:
                    #Renovación Vinculación
                    if type_process == '1':
                        #Si es textilero validar capacidad de prefijos
                        if partner.partner_id.x_sector_id.id == sector_id_textil:
                            capacity_prefixes = partner.total_capacity_prefixes
                            capacity_prefixes = capacity_prefixes.replace('[','').replace(']','')
                            array_capacity_prefixes = capacity_prefixes.split('},')
                            total_capacity_prefixes = 0
                            cant_prefixes = 0
                            bool_insert = False
                            for capacity in array_capacity_prefixes:
                                dict = capacity+'}'
                                dict = dict.replace('}}','}')
                                dict_capacity = eval(dict) 
                                #raise ValidationError(_(dict_capacity))
                                total_capacity_prefixes = total_capacity_prefixes + dict_capacity.get('Capacity')
                                cant_prefixes = cant_prefixes + 1
                                if total_capacity_prefixes >= self.invoicing_companies.textile_code_capability:                           
                                    cant_prefixes_textil_partner.append({'PartnerId':id_contactP,'CantPrefixes':cant_prefixes})
                                    bool_insert = True
                                    break
                            if bool_insert == False:
                                cant_prefixes_textil_partner.append({'PartnerId':id_contactP,'CantPrefixes':cant_prefixes})
                                bool_insert = True
                                
                        #Factura 1: Renovación Aporte Patrimonial corresponde al producto Renovación Aportes Patrimoniales Actividades ECR
                        sale_order_values = {
                            'partner_id' : id_contactP,
                            'partner_invoice_id' : id_contactP,
                            'x_origen': 'FM {}'.format(self.year),
                            'x_type_sale': 'Renovación',
                            'x_conditional_discount': conditional_discount,
                            'x_conditional_discount_deadline': conditional_discount_deadline,
                            'validity_date' : self.invoicing_companies.expiration_date                            
                        }
                        
                        sale_order = self.env['sale.order'].create(sale_order_values)
                        
                        sale_order_line_values = {
                            'order_id' : sale_order.id,
                            'product_id' : product_id,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : unit_fee_value,
                            'discount' : discount                            
                        }
                        
                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                                                
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id                                              
                        }
                        
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                        
                        if type_vinculation == type_vinculation_cliente:
                            saler_orders_partner.append({'PartnerId':id_contactP,'IdFac2':sale_order.id})
                        
                    #Renovación Prefijos Adicionales
                    if type_process == '2':
                        #Si es textilero validar capacidad de prefijos
                        if partner.partner_id.x_sector_id.id == sector_id_textil:
                            #Obtener cantidad a restar de acuerdo a la capacidad
                            cant_resta = 1
                            for cant in cant_prefixes_textil_partner:
                                partner_id = cant['PartnerId']
                                if id_contactP == partner_id:
                                    cant_resta = cant['CantPrefixes']
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (partner.cant_prefixes_ds+partner.cant_prefixes_fixed_weight+partner.cant_prefixes_variable_weight+partner.cant_prefixes_mixed+partner.cant_prefixes_gl)-cant_resta
                            #Al ser textileros se les cobra solamente un porcentaje de cada prefijo pero si el codigo es cedido se cobra el 100%
                            obj_cedidos = self.env['massive.invoicing.codes.assignment'].search([('company_receives.id', '=', partner.partner_id.id)])
                            cant_prefixes_cedidos = 0
                            prefixes_cedidos = []
                            for cedidos in obj_cedidos:
                                prefixes_cedidos.append(cedidos.prefix)
                            
                            cant_prefixes_cedidos = len(prefixes_cedidos)
                            if cant_prefixes != cant_prefixes_cedidos:
                                unit_fee_value = (unit_fee_value/100)*self.invoicing_companies.percentage_textile_tariff                            
                            
                        else:
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (partner.cant_prefixes_ds+partner.cant_prefixes_fixed_weight+partner.cant_prefixes_variable_weight+partner.cant_prefixes_mixed+partner.cant_prefixes_gl)-1
                        #Factura 2: Renovación Prefijos Adicionales (4D a 8D, Peso Fijo y Variable, Mixtos)
                        if cant_prefixes > 0:
                            if type_vinculation == type_vinculation_miembro:
                                sale_order_values = {
                                    'partner_id' : id_contactP,
                                    'partner_invoice_id' : id_contactP,
                                    'x_origen': 'FM {}'.format(self.year),
                                    'x_type_sale': 'Renovación',
                                    'x_conditional_discount': (cant_prefixes+partner.cant_prefixes_gtin)*conditional_discount,
                                    'x_conditional_discount_deadline': conditional_discount_deadline,
                                    'validity_date' : self.invoicing_companies.expiration_date                            
                                }
                                sale_order = self.env['sale.order'].create(sale_order_values)

                                sale_order_line_values = {
                                    'order_id' : sale_order.id,
                                    'product_id' : product_id,
                                    'product_uom_qty' : cant_prefixes, #Cantidad
                                    'price_unit' : unit_fee_value,
                                    'discount' : discount                            
                                }

                                sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)                            
                            
                                saler_orders_partner.append({'PartnerId':id_contactP,'IdFac2':sale_order.id})
                        
                                process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner.partner_id.id)])

                                values_update_process = {
                                    'invoice_two' : sale_order.id                                              
                                }

                                process_partnersaleorder.update(values_update_process)
                                
                            if type_vinculation == type_vinculation_cliente:
                                #Obtener Id Factura 2 que para cliente es solamente 1 factura
                                sale_order_id = 0
                                for sale in saler_orders_partner:
                                    partner_id = sale['PartnerId']
                                    if id_contactP == partner_id:
                                        sale_order_id = sale['IdFac2'] 
                                if sale_order_id != 0:
                                    sale_order_line_values = {
                                        'order_id' : sale_order_id,
                                        'product_id' : product_id,
                                        'product_uom_qty' : cant_prefixes, #Cantidad
                                        'price_unit' : unit_fee_value,
                                        'discount' : discount                            
                                    }

                                    sale_order_line = self.env['sale.order.line'].create(sale_order_line_values) 
                        
                    #Renovación Prefijos GTIN8
                    if type_process == '3':
                        #Cantidad prefijos = Gtin8
                        cant_prefixes = partner.cant_prefixes_gtin    
                        if cant_prefixes > 0:
                            #Obtener Id Factura 2
                            sale_order_id = 0
                            for sale in saler_orders_partner:
                                partner_id = sale['PartnerId']
                                if id_contactP == partner_id:
                                    sale_order_id = sale['IdFac2']                            
                            #Factura 2: Renovación Prefijos GTIN8 (GTIN8)
                            if sale_order_id != 0:
                                sale_order_line_values = {
                                    'order_id' : sale_order_id,
                                    'product_id' : product_id,
                                    'product_uom_qty' : cant_prefixes, #Cantidad
                                    'price_unit' : unit_fee_value,
                                    'discount' : discount                            
                                }
                                
                                sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)                                
                            else:
                                sale_order_values = {
                                    'partner_id' : id_contactP,
                                    'partner_invoice_id' : id_contactP,
                                    'x_origen': 'FM {}'.format(self.year),
                                    'x_type_sale': 'Renovación',
                                    'validity_date' : self.invoicing_companies.expiration_date                            
                                }
                                sale_order = self.env['sale.order'].create(sale_order_values)

                                sale_order_line_values = {
                                    'order_id' : sale_order.id,
                                    'product_id' : product_id,
                                    'product_uom_qty' : cant_prefixes, #Cantidad
                                    'price_unit' : unit_fee_value,
                                    'discount' : discount                            
                                }
                                
                                sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)       
                                
                                saler_orders_partner.append({'PartnerId':id_contactP,'IdFac2':sale_order.id})
                        
                                process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner.partner_id.id)])

                                values_update_process = {
                                    'invoice_two' : sale_order.id                                              
                                }

                                process_partnersaleorder.update(values_update_process)
                                
                
                #Tipos de vinculados diferentes a miembros y clientes
                if type_vinculation != type_vinculation_miembro and type_vinculation != type_vinculation_cliente:
                    #Especial de Empresas GTIN8
                    if partner.partner_id.x_gtin_massive_invoicing == True and type_process == '3':
                        #Cantidad prefijos = Gtin8
                        cant_prefixes = partner.cant_prefixes_gtin    
                        if cant_prefixes > 0:
                            #Factura 1
                            sale_order_values = {
                                'partner_id' : id_contactP,
                                'partner_invoice_id' : id_contactP,
                                'x_origen': 'FM {}'.format(self.year),
                                'x_type_sale': 'Renovación',
                                'x_conditional_discount': conditional_discount,
                                'x_conditional_discount_deadline': conditional_discount_deadline,
                                'validity_date' : self.invoicing_companies.expiration_date                            
                            }

                            sale_order = self.env['sale.order'].create(sale_order_values)                            
                            
                            sale_order_line_values = {
                                'order_id' : sale_order.id,
                                'product_id' : product_id,
                                'product_uom_qty' : cant_prefixes, #Cantidad
                                'price_unit' : unit_fee_value,
                                'discount' : discount                            
                            }

                            sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)            
                                    
class x_MassiveInvoicingEnpointCodeAssignment(models.TransientModel):
    _name = 'massive.invoicing.enpointcodeassignment'
    _description = 'Massive Invoicing - Enpoint Code Assignment'
    
    process_id = fields.Many2one('massive.invoicing.process',string='Proceso FacMasiva', required=True, ondelete='cascade')
    Nit = fields.Char(string='Nit', required=True)
    RazonSocial = fields.Char(string='Razon Social', required=True)
    partner_id = fields.Many2one('res.partner', string='Compañía', required=True)
    type_vinculation = fields.Many2many(string='Tipo de vinculación', readonly=True, related='partner_id.x_type_vinculation')    
    IdEstado = fields.Integer(string='Id Estado', required=True)
    EstadoPrefijo = fields.Char(string='Estado', required=True)
    IdRango = fields.Integer(string='Id Rango', required=True)
    Rango = fields.Char(string='Rango', required=True)
    IdEsquema = fields.Integer(string='Id Esquema', required=True)
    Esquema = fields.Char(string='Esquema', required=True)
    CapacidadPrefijo = fields.Integer(string='Capacidad Prefijo', required=True)
    PrefixId = fields.Char(string='Prefijo', required=True)
    FechaAsignacion = fields.Date(string='Fecha Asignación', required=True)
    
class x_MassiveInvoicingPartnerCalculationPrefixes(models.TransientModel):
    _name = 'massive.invoicing.partnercalculationprefixes'
    _description = 'Massive Invoicing - Partner Calculation Prefixes'
    
    process_id = fields.Many2one('massive.invoicing.process',string='Proceso FacMasiva', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Compañía', required=True)
    type_vinculation = fields.Many2many(string='Tipo de vinculación', readonly=True, related='partner_id.x_type_vinculation')    
    vat = fields.Char(string='Nit', required=True)
    have_prefixes = fields.Selection([
                                        ('1', 'Si'),
                                        ('2', 'No - REVISAR'),                                        
                                    ], string='Tiene códigos', readonly=True)
    
    cant_prefixes_ds = fields.Integer(string='Cant. códigos 4D a 8D', readonly=True) 
    prefixes_ds = fields.Char(string='Códigos 4D a 8D', readonly=True)
    
    cant_prefixes_fixed_weight = fields.Integer(string='Cant. códigos peso fijo', readonly=True) 
    prefixes_fixed_weight = fields.Char(string='Códigos peso fijo', readonly=True)
    
    cant_prefixes_variable_weight = fields.Integer(string='Cant. códigos peso variable', readonly=True) 
    prefixes_variable_weight = fields.Char(string='Códigos peso variable', readonly=True)
    
    cant_prefixes_mixed = fields.Integer(string='Cant. códigos mixtos', readonly=True) 
    prefixes_mixed = fields.Char(string='Códigos mixtos', readonly=True)
    
    cant_prefixes_gtin = fields.Integer(string='Cant. códigos GTIN8', readonly=True) 
    prefixes_gtin = fields.Char(string='Códigos GTIN8', readonly=True)
    
    cant_prefixes_gl = fields.Integer(string='Cant. códigos GLN & GL13', readonly=True) 
    prefixes_gl = fields.Char(string='Códigos GLN & GL13', readonly=True)
    
    total_capacity_prefixes = fields.Char(string='Total de capacidad prefijos', readonly=True)
    
class x_MassiveInvoicingPartnerSaleOrder(models.TransientModel):
    _name = 'massive.invoicing.partner.saleorder'
    _description = 'Massive Invoicing - Partner Sale Order'
    
    process_id = fields.Many2one('massive.invoicing.process',string='Proceso FacMasiva', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Compañía', required=True)
    type_vinculation = fields.Many2many(string='Tipo de vinculación', readonly=True, related='partner_id.x_type_vinculation')    
    sector = fields.Many2one(string='Sector', readonly=True, related='partner_id.x_sector_id')    
    vat = fields.Char(string='Nit', required=True)
    invoice_one = fields.Many2one('sale.order', string='Orden de venta #1', readonly=True)
    invoice_two = fields.Many2one('sale.order', string='Orden de venta #2', readonly=True)
