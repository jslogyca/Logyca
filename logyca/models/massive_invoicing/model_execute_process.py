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
        # process = False
        # process = 'Facturacion masiva'.'utf-8'
        # process = str(process, 'utf-8')
        # body_api = json.dumps({'IsRefact': process, 'Nits': thirdparties})
        body_api = json.dumps({'nit': thirdparties, 'proceso': 'Facturación masiva'})
        headers_api = {'content-type': 'application/json'}
        url_api = self.invoicing_companies.url_enpoint_code_assignment
        # url_api = "https://asctestdocker.azurewebsites.net/codes/fr_masivo/"
        # response = requests.get(url_api,data=body_api, headers=headers_api)

        payload = {'nit': thirdparties, 'proceso': 'Facturación masiva'}

        response = requests.post(url_api, data=json.dumps(payload))

        # print('URL', url_api)
        # print('BODY APIaaa', body_api)
        # print('HEADERS', headers_api)
        # print('RESPONSE', response)
        # print('STATUS', response.status_code)
        result = response.json()
        # print('RESPONSE 2222', result)

        #Eliminar llamado si ya existe
        enpointcodeassignment_exists = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', self.id)])
        enpointcodeassignment_exists.unlink()

        result = response.json()
        # print('RESPONSE 935856565656', result.values())
        # print('RESPONSE 935856565656', type(result.values()))
        # print('RESPONSE 141414151515', result.items())
        # print('RESPONSE 141414151515', type(result.items()))
        # print('RESPONSE 161616161616', result["data"])

        response.close()
        # print('RESPONSE 656565656565', len(result.values()))
        # print('RESPONSE 656565656565', len(result.items()))
        enpointcodeassignment_vals2=None
        for data in result["data"]:
            print('RESPONSE 656565656565', data)          
            if data['Info Prefijos']:
                for prefijo in data['Info Prefijos']: 
                    partner_vat = data['Nit']
                    # enpointcodeassignment_vals2 = data
                    # enpointcodeassignment_vals2['process_id'] = self.id                       
                    print('PREFIJO 888888877777', prefijo)
                    enpointcodeassignment_vals2 = {
                        'process_id': self.id,
                        'Nit': data['Nit'],
                        'RazonSocial': data['Razon social'],
                        'IdEstado': prefijo['Codigo estado'],
                        'EstadoPrefijo': prefijo['Descripcion estado'],
                        'IdRango': prefijo['Codigo rango'],
                        'Rango': prefijo['Rango descripcion'],
                        'Esquema': prefijo['Esquema'],
                        'CapacidadPrefijo': prefijo['Capacidad'],
                        'PrefixId': prefijo['Prefijo'],
                        'FechaAsignacion': '2021-12-31',
                    }

                    if prefijo['Esquema']=='Renovación anual a 31 de diciembre':
                        enpointcodeassignment_vals2['IdEsquema'] = 1
                    if prefijo['Esquema']=='Renovación anual a 31 de diciembre GS1':
                        enpointcodeassignment_vals2['IdEsquema'] = 6
                    if prefijo['Esquema']=='Renovación cliente prefijo':
                        enpointcodeassignment_vals2['IdEsquema'] = 7
                    self._cr.execute(''' select p.id
                                            from massive_invoicing_companies_res_partner_rel r
                                            inner join res_partner p on p.id=r.res_partner_id
                                            where massive_invoicing_companies_id=%s and p.vat=%s ''', (self.invoicing_companies.id, partner_vat))
                    partner_id = self._cr.fetchone()
                    enpointcodeassignment_vals2['partner_id'] = partner_id[0]
                    # for partner in self.invoicing_companies.thirdparties:
                    #     if partner.vat == partner_vat:
                    #         partner_id = partner.id
                    #         # enpointcodeassignment_vals['partner_id'] = partner_id
                    #         enpointcodeassignment_vals2['partner_id'] = partner_id

                    enpointcodeassignment = self.env['massive.invoicing.enpointcodeassignment'].create(enpointcodeassignment_vals2)
                    self.env.cr.commit()
                if len(data['Info Prefijos'])>1:
                    print('PREFIJO 752525252', enpointcodeassignment_vals2)
                    print('RESPONSE 656565656565', data['Info Prefijos'])
                    print('RESPONSE 656565656565', len(data['Info Prefijos']))                          
            else:
                continue
                # enpointcodeassignment_vals2 = {
                #     'process_id': self.id,
                #     'Nit': data['Nit'],
                #     'RazonSocial': data['Razon social'],
                #     'IdEstado': data['Info Prefijos']['Codigo estado'],
                #     'EstadoPrefijo': data['Info Prefijos']['Descripcion estado'],
                #     'IdRango': data['Info Prefijos']['Codigo rango'],
                #     'Rango': data['Info Prefijos']['Rango descripcion'],
                #     'IdEsquema': 2,
                #     'Esquema': data['Info Prefijos']['Renovación anual a 31 de diciembre GS1'],
                #     'CapacidadPrefijo': data['Info Prefijos']['Capacidad'],
                #     'PrefixId': data['Info Prefijos']['PrefixId'],
                #     'FechaAsignacion': '2021-12-31',
                # }          
    # {'Nit': '79278214', 'Razon social': 'EDUARDO GOMEZ  NEIRA', 'Info Prefijos': [{'Prefijo': 7707900648, 'Codigo estado': 2, 
    # 'Descripcion estado': 'Asignado', 'Codigo rango': 5, 'Rango descripcion': '7D', 
    # 'Esquema': 'Renovación anual a 31 de diciembre GS1', 'Capacidad': 100, 'PrefixId': 1587}]}, 
            for partner in self.invoicing_companies.thirdparties:
                if partner.vat == partner_vat:
                    partner_id = partner.id
                    # enpointcodeassignment_vals['partner_id'] = partner_id
                    enpointcodeassignment_vals2['partner_id'] = partner_id
             
            #raise ValidationError(_(enpointcodeassignment_vals))
            # print('VALORES', enpointcodeassignment_vals2)
            # enpointcodeassignment = self.env['massive.invoicing.enpointcodeassignment'].create(enpointcodeassignment_vals2)
            
        return response.json()
    
    #Cálculo de cantidad de prefijos
    def calculation_of_number_prefixes(self):  
        
        #Eliminar llamado si ya existe
        partnercalculationprefixes_exists = self.env['massive.invoicing.partnercalculationprefixes'].search([('process_id', '=', self.id)])
        partnercalculationprefixes_exists.unlink()
        
        for partner in self.invoicing_companies.thirdparties:
            prefixes_ds = []
            cant_prefixes_ds = 0
            prefixes_cp_ds = []
            cant_prefixes_cp_ds = 0
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
                partner_esquema = data.Esquema
                total_capacity_prefixes.append({'Rango':partner_range,'Capacity':data.CapacidadPrefijo})
                                
                if partner_range in ['4D','5D','6D','7D','8D']:
                    if partner_esquema == 'Renovación cliente prefijo':
                        prefixes_cp_ds.append(data.PrefixId)
                    else:
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
            cant_prefixes_cp_ds = len(prefixes_cp_ds)
            cant_prefixes_fixed_weight = len(prefixes_fixed_weight)
            cant_prefixes_variable_weight = len(prefixes_variable_weight)
            cant_prefixes_mixed = len(prefixes_mixed)
            cant_prefixes_gtin = len(prefixes_gtin)
            cant_prefixes_gl = len(prefixes_gl)
            
            if cant_prefixes_ds+cant_prefixes_cp_ds+cant_prefixes_fixed_weight+cant_prefixes_variable_weight+cant_prefixes_mixed+cant_prefixes_gtin+cant_prefixes_gl > 0:
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
                'cant_prefixes_cp_ds': cant_prefixes_cp_ds,
                'prefixes_cp_ds': str(prefixes_cp_ds),
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
    def execute_process_ant(self):
        #Eliminar ordenes de venta si ya existen solamente cuando se ejecute facturación masiva general y no adicional
        if self.invoicing_companies.process_type == '1':
            saleorder_exists = self.env['sale.order'].search([('x_origen', '=', 'FM {}'.format(self.year))])
            saleorder_exists.unlink()
        process_partnersaleorder_exists = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id)])
        process_partnersaleorder_exists.unlink()
        #Tipos de vinculación Miembro y CLiente
        type_vinculation_miembro = 0
        type_vinculation_miembro_c = 0
        type_vinculation_miembro_i = 0
        type_vinculation_miembro_f = 0
        type_vinculation_cliente = 0
        type_vinculation_prefijo = 0
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_miembros_c = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro por convenio')])
        obj_type_vinculation_miembros_i = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembros Internacionales')])
        obj_type_vinculation_miembros_f = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro Filial')])        
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        obj_type_vinculation_prefijo = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente Prefijo')])
        for m in obj_type_vinculation_miembros:
            type_vinculation_miembro = m.id
        for mc in obj_type_vinculation_miembros_c:
            type_vinculation_miembro_c = mc.id
        for mi in obj_type_vinculation_miembros_i:
            type_vinculation_miembro_i = mi.id
        for mf in obj_type_vinculation_miembros_f:
            type_vinculation_miembro_f = mf.id
        for c in obj_type_vinculation_cliente:
            type_vinculation_cliente = c.id
        for p in obj_type_vinculation_prefijo:
            type_vinculation_prefijo = p.id
        #Traer el sector de textileros
        sector_id_textil = 10 #Id definido, en caso de camviar revisar la tabla de sectores de Logyca
        #Traer los productos y sus tipos de proceso
        saler_orders_partner = []
        cant_prefixes_textil_partner = []
        if self.invoicing_companies.process_type == '1':
            obj_massive_invoicing_products = self.env['massive.invoicing.products'].search([('product_id', '!=', False)])
        else:
            obj_massive_invoicing_products = self.env['massive.invoicing.products'].search([('product_id', '!=', False),('type_process', '=', '5')])
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
                        
                # obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                if partner.partner_id.fact_annual == 'activos':
                    obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                else:
                    if partner.partner_id.fact_annual == 'ingresos':
                        obj_tariff = self.env['massive.income.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('revenue_range','=',partner.partner_id.x_income_range.id),('product_id','=',product_id)])
                for tariff in obj_tariff:
                    fee_value = tariff.fee_value
                    unit_fee_value = tariff.unit_fee_value
                    partner_logycaedx = self.env['partner.logycaedx'].search([('partner_id', '=', partner.partner_id.id), ('year', '=', self.year)])
                    partner_logyca_revenue = self.env['partner.logyca.revenue'].search([('partner_id', '=', partner.partner_id.id), ('year', '=', self.year)])
                    if partner_logycaedx and type_process == '1':
                        #Logica descuento no condicionado
                        if partner_logycaedx.config_discount_id.discount > 0:
                            discount = partner_logycaedx.config_discount_id.discount
                    elif partner_logyca_revenue and type_process == '1':
                        #Logica descuento no condicionado
                        if partner_logyca_revenue.config_discount_id.discount > 0:
                            discount = partner_logyca_revenue.config_discount_id.discount
                    else:
                        obj_tariff_discounts = self.env['massive.invoicing.tariff.discounts'].search([('tariff', '=', tariff.id)])
                        for tariff_discounts in obj_tariff_discounts:
                            #Logica descuento no condicionado
                            if tariff_discounts.discount_percentage > 0:
                                discount = tariff_discounts.discount_percentage
                            #Logica descuento condicionado
                            if tariff_discounts.discounts_one > 0:
                                conditional_discount = tariff_discounts.discounts_one 
                                conditional_discount_deadline = tariff_discounts.date_discounts_one
                        # DESCUENTO INGRESOS
                        obj_tariff_in_discounts = self.env['massive.income.tariff.discounts'].search([('tariff', '=', tariff.id)])
                        for tariff_discounts in obj_tariff_in_discounts:
                            #Logica descuento no condicionado
                            if tariff_discounts.discount_percentage > 0:
                                discount = tariff_discounts.discount_percentage
                            #Logica descuento condicionado
                            if tariff_discounts.discounts_one > 0:
                                conditional_discount = tariff_discounts.discounts_one 
                                conditional_discount_deadline = tariff_discounts.date_discounts_one                                
                #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                id_contactP = 0
                id_contactPt=0
                for record in partner.partner_id.child_ids:   
                    ls_contacts = record.x_contact_type
                    for i in ls_contacts:
                        if i.id == 2:
                            id_contactP = record.id
                            id_contactPt = partner.partner_id.id
                    
                if id_contactP == 0:
                    id_contactP = partner.partner_id.id
                    id_contactPt = partner.partner_id.id
                    
                #Clientes / Miembros.
                if type_vinculation == type_vinculation_miembro or type_vinculation == type_vinculation_cliente \
                            or type_vinculation == type_vinculation_miembro_c or type_vinculation == type_vinculation_miembro_i or type_vinculation == type_vinculation_miembro_f:
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

                #Tipos de vinculados Cliente Prefijo
                if type_vinculation != type_vinculation_miembro and type_vinculation != type_vinculation_cliente and type_vinculation_prefijo:
                    cant_prefixes = (partner.cant_prefixes_ds+partner.cant_prefixes_fixed_weight+partner.cant_prefixes_variable_weight+partner.cant_prefixes_mixed+partner.cant_prefixes_gl)
                    if cant_prefixes == 1:
                        prefix_id = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', partner.process_id.id),
                                                                                                ('partner_id', '=', partner.partner_id.id)], order="id asc", limit=1)
                        tariff_prefix_id = self.env['massive.tariff.prefix'].search([('year', '=', partner.process_id.year),
                                                                                        ('type_prefix', '=', prefix_id.Rango)], order="id asc", limit=1)
                        if tariff_prefix_id:                                                                               
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
                                'name' : process.product_id.name + ' ' + prefix_id.Rango,
                                'product_uom_qty' : cant_prefixes, #Cantidad
                                'price_unit' : tariff_prefix_id.fee_value,
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

                    if cant_prefixes > 1:
                        prefix_id = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', partner.process_id.id),
                                                                                                ('partner_id', '=', partner.partner_id.id)], order="id asc")
                        for pre in prefix_id:
                            tariff_prefix_id = self.env['massive.tariff.prefix'].search([('year', '=', partner.process_id.year),
                                                                                            ('type_prefix', '=', pre.Rango)], order="id asc", limit=1)
                            if tariff_prefix_id:                                                                               
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
                                    'name' : process.product_id.name + ' ' + pre.Rango,
                                    'product_uom_qty' : cant_prefixes, #Cantidad
                                    'price_unit' : tariff_prefix_id.fee_value,
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

                    #Renovación Prefijos GTIN8
                
                if type_process == '5':
                    invoice=None
                    invoice_pm=None
                    invoice_pc=None
                    invoice_gt=None
                    invoice_ce=None
                    invoice_p=None
                    if  product_id == 3:
                        invoice = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',27),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice:
                            invoice = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',27),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])
                    if  product_id == 274:
                        invoice_pm = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',273),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice_pm:
                            invoice_pm = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',273),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])
                    if  product_id == 1666:
                        invoice_pc = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',1480),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice_pc:
                            invoice_pc = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',1480),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])
                    if  product_id == 276:
                        invoice_gt = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',271),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice_gt:
                            invoice_gt = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',271),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])
                    if  product_id == 275:
                        invoice_ce = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',272),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice_ce:
                            invoice_ce = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',272),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])

                    if  product_id == 1745:
                        invoice_p = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactP),
                                                                            ('move_id.x_is_mass_billing','=',True),
                                                                            ('product_id','=',1744),
                                                                            ('date','>=','2024-01-01'),
                                                                                ('move_id.payment_state','=','not_paid'),])
                        if not invoice_p:    
                            invoice_p = self.env['account.move.line'].search([('move_id.partner_id', '=', id_contactPt),
                                                                                ('move_id.x_is_mass_billing','=',True),
                                                                                ('product_id','=',1744),
                                                                                ('date','>=','2024-01-01'),
                                                                                    ('move_id.payment_state','=','not_paid'),])


                                                                                
                    if invoice:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                    elif invoice_pm:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice_pm.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                    elif invoice_pc:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice_pc.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                    elif invoice_gt:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice_gt.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                    elif invoice_ce:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice_ce.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)
                    elif invoice_p:
                        #Factura 1
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
                            'name' : process.product_id.name,
                            'product_uom_qty' : 1, #Cantidad
                            'price_unit' : round(((invoice_p.move_id.amount_untaxed*5)/100),2)
                        }

                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
                        values_save_process = {
                            'process_id' : self.id,
                            'partner_id' : partner.partner_id.id,
                            'vat' : partner.partner_id.vat,
                            'invoice_one' : sale_order.id
                        }
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)

    def _create_sale_order_add_aport(self, partner_company, conditional_discount, 
                            product_id, product_uom_qty, unit_fee_value, discount, invoice_id):
        #Factura 1: Renovación Aporte Patrimonial corresponde al producto Renovación Aportes Patrimoniales Actividades ECR
        sale_order_values = {
            'partner_id' : partner_company.id,
            'client_order_ref' : 'Por factura sin pago ' + invoice_id.name,
            'partner_invoice_id' : partner_company.id,
            'x_origen': 'FM {}'.format(self.year),
            'x_type_sale': 'Renovación',
            'x_conditional_discount': conditional_discount,
            'x_conditional_discount_deadline': None,
            'validity_date' : self.invoicing_companies.expiration_date                            
        }
        
        sale_order = self.env['sale.order'].create(sale_order_values)
        
        sale_order_line_values = {
            'order_id' : sale_order.id,
            'product_id' : product_id.id,
            'product_uom_qty' : product_uom_qty, #Cantidad
            'price_unit' : unit_fee_value,
            'discount' : discount                            
        }
        
        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)

        values_save_process = {
            'process_id' : self.id,
            'partner_id' : partner_company.id,
            'vat' : partner_company.vat,
            'invoice_one' : sale_order.id                                              
        }
        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)        
        return True                        

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
        type_vinculation_miembro_c = 0
        type_vinculation_miembro_i = 0
        type_vinculation_miembro_f = 0
        type_vinculation_cliente = 0
        type_vinculation_prefijo = 0
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_miembros_c = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro por convenio')])
        obj_type_vinculation_miembros_i = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembros Internacionales')])
        obj_type_vinculation_miembros_f = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro Filial')])        
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        obj_type_vinculation_prefijo = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente Prefijo')])
        for m in obj_type_vinculation_miembros:
            type_vinculation_miembro = m.id
        for mc in obj_type_vinculation_miembros_c:
            type_vinculation_miembro_c = mc.id
        for mi in obj_type_vinculation_miembros_i:
            type_vinculation_miembro_i = mi.id
        for mf in obj_type_vinculation_miembros_f:
            type_vinculation_miembro_f = mf.id
        for c in obj_type_vinculation_cliente:
            type_vinculation_cliente = c.id
        for p in obj_type_vinculation_prefijo:
            type_vinculation_prefijo = p.id
        #Traer el sector de textileros
        sector_id_textil = 10 #Id definido, en caso de camviar revisar la tabla de sectores de Logyca
        #Traer los productos y sus tipos de proceso
        saler_orders_partner = []
        cant_prefixes_textil_partner = []
        if self.invoicing_companies.process_type == '1':
            obj_massive_products_reno = self.env['massive.invoicing.products'].search([('product_id', '=', 27)])
            obj_massive_products_padic = self.env['massive.invoicing.products'].search([('product_id', '=', 273)])
            obj_massive_products_padicl = self.env['massive.invoicing.products'].search([('product_id', '=', 272)])
            obj_massive_products_cliepre = self.env['massive.invoicing.products'].search([('product_id', '=', 1744)])
            obj_massive_products_gtin = self.env['massive.invoicing.products'].search([('product_id', '=', 271)])
        else:
            obj_massive_invoicing_products = self.env['massive.invoicing.products'].search([('product_id', '!=', False),('type_process', '=', '5')])
        obj_company = self.env['massive.invoicing.partnercalculationprefixes'].search([('process_id', '=', self.id),('have_prefixes','=','1')])
        discount_pref = 0
        for partner_company in self.invoicing_companies.thirdparties:
            if self.invoicing_companies.process_type == '2':
                invoice_ids = self.env['account.move'].search([('partner_id', '=', partner_company.id),
                                                                ('x_is_mass_billing', '=', True),
                                                                ('date', '>=', '2025-01-01'),
                                                                ('payment_state', '=', 'not_paid'),
                                                                ('state', '=', 'posted'),
                                                                ('move_type', '=', 'out_invoice')])
                invoice_ids += self.env['account.move'].search([('partner_id.parent_id', '=', partner_company.id),
                                                                ('x_is_mass_billing', '=', True),
                                                                ('date', '>=', '2025-01-01'),
                                                                ('payment_state', '=', 'not_paid'),
                                                                ('state', '=', 'posted'),
                                                                ('move_type', '=', 'out_invoice')])
                print('FACTURAS', invoice_ids)                                                                
                if invoice_ids:
                    for invoice_id in invoice_ids:
                        for line in invoice_id.invoice_line_ids:
                            if line.product_id.id == 27:
                                obj_massive_products = self.env['massive.invoicing.products'].search([('product_id', '=', 3)])
                                self._create_sale_order_add_aport(partner_company, 0, 
                                        obj_massive_products.product_id, 1, (line.price_unit*0.05), 0, invoice_id)
                            if line.product_id.id == 1744:
                                obj_massive_products = self.env['massive.invoicing.products'].search([('product_id', '=', 1745)])
                                self._create_sale_order_add_aport(partner_company, 0, 
                                        obj_massive_products.product_id, 1, (invoice_id.amount_untaxed*0.05), 0, invoice_id)
                                break
                            if line.product_id.id == 271 and len(invoice_id.invoice_line_ids) == 1:
                                obj_massive_products = self.env['massive.invoicing.products'].search([('product_id', '=', 276)])
                                self._create_sale_order_add_aport(partner_company, 0, 
                                        obj_massive_products.product_id, 1, (invoice_id.amount_untaxed*0.05), 0, invoice_id)
                                break
                            if line.product_id.id == 273 and len(invoice_id.invoice_line_ids) == 1:
                                obj_massive_products = self.env['massive.invoicing.products'].search([('product_id', '=', 274)])
                                self._create_sale_order_add_aport(partner_company, 0, 
                                        obj_massive_products.product_id, 1, (invoice_id.amount_untaxed*0.05), 0, invoice_id)
                                break
                continue
            is_member = False
            for vinculation in partner_company.x_type_vinculation:
                print('EMPRESA SELECCIONADA', vinculation.name, partner_company.name)
                if vinculation.name in ('Miembro','Miembro por convenio','Miembros Internacionales','Miembro Filial'):
                    is_member = True
                    print('EMPRESA MIEMBRO', vinculation.name, partner_company.name)
                    fee_value = 0
                    unit_fee_value = 0
                    discount = 0                       
                    conditional_discount = 0
                    conditional_discount_deadline = False
                    # obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                    print('RENOVACIÓN APORTES MIEMBRO TARIFA ACTIVOS', partner_company.fact_annual, self.year, vinculation.name,  partner_company, partner_company.x_asset_range.name, obj_massive_products_reno.product_id.name)
                    print('RENOVACIÓN APORTES MIEMBRO TARIFA ACTIVOS', partner_company.fact_annual, self.year, vinculation.id,  partner_company, partner_company.x_asset_range.id, obj_massive_products_reno.id)
                    print('RENOVACIÓN APORTES MIEMBRO TARIFA INGRESOS', partner_company.fact_annual, self.year, vinculation.name,  partner_company, partner_company.x_income_range.amount, obj_massive_products_reno.product_id.name)
                    if partner_company.fact_annual == 'activos':
                        obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',vinculation.id),
                                                            ('asset_range','=',partner_company.x_asset_range.id),('product_id','=',obj_massive_products_reno.product_id.id)])
                    else:
                        if partner_company.fact_annual == 'ingresos':
                            obj_tariff = self.env['massive.income.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',vinculation.id),
                                                            ('revenue_range','=',partner_company.x_income_range.id),
                                                            ('product_id','=',obj_massive_products_reno.product_id.id)])
                    print('TARIFA', obj_tariff)
                    for tariff in obj_tariff:
                        fee_value = tariff.fee_value
                        unit_fee_value = tariff.unit_fee_value
                        partner_logycaedx = self.env['partner.logycaedx'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        partner_logyca_revenue = self.env['partner.logyca.revenue'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        if partner_logycaedx:
                            #Logica descuento no condicionado
                            if partner_logycaedx.config_discount_id.discount > 0:
                                discount = partner_logycaedx.config_discount_id.discount
                        elif partner_logyca_revenue:
                            #Logica descuento no condicionado
                            if partner_logyca_revenue.config_discount_id.discount > 0:
                                discount = partner_logyca_revenue.config_discount_id.discount
                        else:
                            obj_tariff_discounts = self.env['massive.invoicing.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                            # DESCUENTO INGRESOS
                            obj_tariff_in_discounts = self.env['massive.income.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_in_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                    #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                    id_contactP = 0
                    id_contactPt=0
                    for record in partner_company.child_ids:   
                        ls_contacts = record.x_contact_type
                        for i in ls_contacts:
                            if i.id == 2:
                                id_contactP = record.id
                                id_contactPt = partner_company.id
                        
                    if id_contactP == 0:
                        id_contactP = partner_company.id
                        id_contactPt = partner_company.id
                            
                    #Factura 1: Renovación Aporte Patrimonial corresponde al producto Renovación Aportes Patrimoniales Actividades ECR
                    print('RENOVACIÓN APORTES MIEMBRO', unit_fee_value, partner_company)
                    self._create_sale_order_fm_aport(partner_company, id_contactP, conditional_discount, 
                            conditional_discount_deadline, obj_massive_products_reno.product_id, 1, unit_fee_value, discount)
                    #Factura 2: Prefijos Adicionales
                    prefixes_company = obj_company.filtered(lambda pref: pref.partner_id == partner_company)
                    print('EMPRESA PREFIJOS MIEMBROS', prefixes_company)
                    if prefixes_company :
                        print('EMPRESA PREFIJOS MIEMBROS 3333', prefixes_company)
                        if partner_company.x_sector_id.id == sector_id_textil:
                            capacity_prefixes = prefixes_company.total_capacity_prefixes
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

                            #Renovación Prefijos Adicionales y Prefijos
                            #Si es textilero validar capacidad de prefijos
                        if partner_company.x_sector_id.id == sector_id_textil:
                            #Obtener cantidad a restar de acuerdo a la capacidad
                            cant_resta = 1
                            for cant in cant_prefixes_textil_partner:
                                partner_id = cant['PartnerId']
                                if id_contactP == partner_id:
                                    cant_resta = cant['CantPrefixes']
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)-cant_resta
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                            #Al ser textileros se les cobra solamente un porcentaje de cada prefijo pero si el codigo es cedido se cobra el 100%
                            obj_cedidos = self.env['massive.invoicing.codes.assignment'].search([('company_receives.id', '=', partner_company.id)])
                            cant_prefixes_cedidos = 0
                            prefixes_cedidos = []
                            for cedidos in obj_cedidos:
                                prefixes_cedidos.append(cedidos.prefix)
                            
                            cant_prefixes_cedidos = len(prefixes_cedidos)
                            if cant_prefixes != cant_prefixes_cedidos:
                                unit_fee_value = (unit_fee_value/100)*self.invoicing_companies.percentage_textile_tariff                            
                            
                        else:
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)-1
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                        #Factura 2: Renovación Prefijos Adicionales (4D a 8D, Peso Fijo y Variable, Mixtos)

                        print('PREFIJOS -------', cant_prefixes_cp)
                        print('PREFIJOS ADICIONALES -------', cant_prefixes)
                        print('PREFIJOS ADICIONALES GTIN -------', prefixes_company.cant_prefixes_gtin)

                        if cant_prefixes > 0 or prefixes_company.cant_prefixes_gtin > 0:
                            print('EMPRESA PREFIJOS ADICONALES MIEMBROS 44444', cant_prefixes)
                            conditional_discount = (cant_prefixes+prefixes_company.cant_prefixes_gtin)*conditional_discount
                            sale_pa = self._create_sale_order_fm(vinculation, partner_company, id_contactP, conditional_discount, 
                                    conditional_discount_deadline, obj_massive_products_padic.product_id, cant_prefixes, unit_fee_value, 
                                    discount, prefixes_company.cant_prefixes_gtin , obj_massive_products_gtin.product_id)

                            process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                            values_update_process = {
                                'invoice_two' : sale_pa.id                                              
                            }

                            process_partnersaleorder.update(values_update_process)                                    
                        
                        if cant_prefixes_cp > 0:
                            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 55555', cant_prefixes_cp)
                            
                            sale = self._create_sale_order_fm_pm(partner_company, id_contactP, conditional_discount, 
                                    conditional_discount_deadline, obj_massive_products_cliepre.product_id, cant_prefixes_cp, unit_fee_value, 
                                    discount)
                            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555552', cant_prefixes_cp)
                            process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                            values_update_process = {
                                'invoice_two' : sale.id                                              
                            }

                            process_partnersaleorder.update(values_update_process)
                    else:
                        continue
                if vinculation.name in ('Cliente Prefijo'):
                    if is_member:
                        continue
                    print('EMPRESA CLIENTE PREFIJO', partner_company.x_type_vinculation.name, partner_company.name)
                    fee_value = 0
                    unit_fee_value = 0
                    discount = 0                       
                    conditional_discount = 0
                    conditional_discount_deadline = False
                            
                    # obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                    if partner_company.fact_annual == 'activos':
                        obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',partner_company.x_type_vinculation.id),
                                                            ('asset_range','=',partner_company.x_asset_range.id),('product_id','=',obj_massive_products_reno.id)])
                    else:
                        if partner_company.fact_annual == 'ingresos':
                            obj_tariff = self.env['massive.income.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',partner_company.x_type_vinculation.id),
                                                            ('revenue_range','=',partner_company.x_income_range.id),
                                                            ('product_id','=',obj_massive_products_reno.id)])
                    for tariff in obj_tariff:
                        fee_value = tariff.fee_value
                        unit_fee_value = tariff.unit_fee_value
                        partner_logycaedx = self.env['partner.logycaedx'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        partner_logyca_revenue = self.env['partner.logyca.revenue'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        if partner_logycaedx:
                            #Logica descuento no condicionado
                            if partner_logycaedx.config_discount_id.discount > 0:
                                discount = partner_logycaedx.config_discount_id.discount
                        elif partner_logyca_revenue:
                            #Logica descuento no condicionado
                            if partner_logyca_revenue.config_discount_id.discount > 0:
                                discount = partner_logyca_revenue.config_discount_id.discount
                        else:
                            obj_tariff_discounts = self.env['massive.invoicing.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                            # DESCUENTO INGRESOS
                            obj_tariff_in_discounts = self.env['massive.income.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_in_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                    #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                    id_contactP = 0
                    id_contactPt=0
                    for record in partner_company.child_ids:   
                        ls_contacts = record.x_contact_type
                        for i in ls_contacts:
                            if i.id == 2:
                                id_contactP = record.id
                                id_contactPt = partner_company.id
                        
                    if id_contactP == 0:
                        id_contactP = partner_company.id
                        id_contactPt = partner_company.id

                    prefixes_company = obj_company.filtered(lambda pref: pref.partner_id == partner_company)
                    print('EMPRESA PREFIJOS CLIENTE PREFIJO', prefixes_company)
                    if prefixes_company:
                        cant_prefixes = 0
                        cant_prefixes_cp = 0
                        if partner_company.x_sector_id.id == sector_id_textil:
                            capacity_prefixes = prefixes_company.total_capacity_prefixes
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

                            #Renovación Prefijos Adicionales y Prefijos
                            #Si es textilero validar capacidad de prefijos
                        if partner_company.x_sector_id.id == sector_id_textil:
                            #Obtener cantidad a restar de acuerdo a la capacidad
                            cant_resta = 1
                            for cant in cant_prefixes_textil_partner:
                                partner_id = cant['PartnerId']
                                if id_contactP == partner_id:
                                    cant_resta = cant['CantPrefixes']
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)-cant_resta
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)-cant_resta
                            #Al ser textileros se les cobra solamente un porcentaje de cada prefijo pero si el codigo es cedido se cobra el 100%
                            obj_cedidos = self.env['massive.invoicing.codes.assignment'].search([('company_receives.id', '=', partner_company.id)])
                            cant_prefixes_cedidos = 0
                            prefixes_cedidos = []
                            for cedidos in obj_cedidos:
                                prefixes_cedidos.append(cedidos.prefix)
                            
                            cant_prefixes_cedidos = len(prefixes_cedidos)
                            if cant_prefixes != cant_prefixes_cedidos:
                                unit_fee_value = (unit_fee_value/100)*self.invoicing_companies.percentage_textile_tariff                            
                            
                        else:
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)-1
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                        #Factura 2: Renovación Prefijos Adicionales (4D a 8D, Peso Fijo y Variable, Mixtos)
                        if cant_prefixes > 0 or prefixes_company.cant_prefixes_gtin > 0:
                            print('EMPRESA PREFIJOS ADICONALES CLIENTE PREFIJO 44444', cant_prefixes)
                            conditional_discount = (cant_prefixes+prefixes_company.cant_prefixes_gtin)*conditional_discount
                            sale_pa = self._create_sale_order_fm(vinculation, partner_company, id_contactP, conditional_discount, 
                                    conditional_discount_deadline, obj_massive_products_padic.product_id, cant_prefixes, unit_fee_value, 
                                    discount, prefixes_company.cant_prefixes_gtin , obj_massive_products_gtin.product_id)

                            process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                            values_update_process = {
                                'invoice_two' : sale_pa.id                                              
                            }

                            process_partnersaleorder.update(values_update_process)                                    
                        
                        if cant_prefixes_cp > 0:
                            print('EMPRESA PREFIJOS CLIENTE CLIENTE PREFIJO 55555', cant_prefixes_cp)
                            
                            sale = self._create_sale_order_fm_pm(partner_company, id_contactP, conditional_discount, 
                                    conditional_discount_deadline, obj_massive_products_cliepre.product_id, cant_prefixes_cp, unit_fee_value, 
                                    discount)
                            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555552', cant_prefixes_cp)
                            process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                            values_update_process = {
                                'invoice_two' : sale.id                                              
                            }

                            process_partnersaleorder.update(values_update_process)
                    else:
                        continue
                if vinculation.name in ('Cliente'):
                    print('EMPRESA CLIENTE', partner_company.x_type_vinculation.name, partner_company.name)
                    fee_value = 0
                    unit_fee_value = 0
                    discount = 0                       
                    conditional_discount = 0
                    conditional_discount_deadline = False
                            
                    # obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),('type_vinculation','=',type_vinculation),('asset_range','=',partner.partner_id.x_asset_range.id),('product_id','=',product_id)])
                    if partner_company.fact_annual == 'activos':
                        obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',partner_company.x_type_vinculation.id),
                                                            ('asset_range','=',partner_company.x_asset_range.id),('product_id','=',obj_massive_products_padicl.product_id.id)])
                    else:
                        if partner_company.fact_annual == 'ingresos':
                            obj_tariff = self.env['massive.income.tariff'].search([('year', '=', self.year),
                                                            ('type_vinculation','=',partner_company.x_type_vinculation.id),
                                                            ('revenue_range','=',partner_company.x_income_range.id),
                                                            ('product_id','=', obj_massive_products_padicl.product_id.id)])
                    for tariff in obj_tariff:
                        fee_value = tariff.fee_value
                        unit_fee_value = tariff.unit_fee_value
                        partner_logycaedx = self.env['partner.logycaedx'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        partner_logyca_revenue = self.env['partner.logyca.revenue'].search([('partner_id', '=', partner_company.id), ('year', '=', self.year)])
                        if partner_logycaedx:
                            #Logica descuento no condicionado
                            if partner_logycaedx.config_discount_id.discount > 0:
                                discount = partner_logycaedx.config_discount_id.discount
                        elif partner_logyca_revenue:
                            #Logica descuento no condicionado
                            if partner_logyca_revenue.config_discount_id.discount > 0:
                                discount = partner_logyca_revenue.config_discount_id.discount
                        else:
                            obj_tariff_discounts = self.env['massive.invoicing.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                            # DESCUENTO INGRESOS
                            obj_tariff_in_discounts = self.env['massive.income.tariff.discounts'].search([('tariff', '=', tariff.id)])
                            for tariff_discounts in obj_tariff_in_discounts:
                                #Logica descuento no condicionado
                                if tariff_discounts.discount_percentage > 0:
                                    discount = tariff_discounts.discount_percentage
                                #Logica descuento condicionado
                                if tariff_discounts.discounts_one > 0:
                                    conditional_discount = tariff_discounts.discounts_one 
                                    conditional_discount_deadline = tariff_discounts.date_discounts_one
                    #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                    id_contactP = 0
                    id_contactPt=0
                    for record in partner_company.child_ids:   
                        ls_contacts = record.x_contact_type
                        for i in ls_contacts:
                            if i.id == 2:
                                id_contactP = record.id
                                id_contactPt = partner_company.id
                        
                    if id_contactP == 0:
                        id_contactP = partner_company.id
                        id_contactPt = partner_company.id

                    prefixes_company = obj_company.filtered(lambda pref: pref.partner_id == partner_company)
                    print('EMPRESA PREFIJOS', prefixes_company)
                    if prefixes_company:
                        if partner_company.x_sector_id.id == sector_id_textil:
                            capacity_prefixes = prefixes_company.total_capacity_prefixes
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

                        #Renovación Prefijos Adicionales y Prefijos
                        #Si es textilero validar capacidad de prefijos
                        if partner_company.x_sector_id.id == sector_id_textil:
                            #Obtener cantidad a restar de acuerdo a la capacidad
                            cant_resta = 1
                            for cant in cant_prefixes_textil_partner:
                                partner_id = cant['PartnerId']
                                if id_contactP == partner_id:
                                    cant_resta = cant['CantPrefixes']
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                            #Al ser textileros se les cobra solamente un porcentaje de cada prefijo pero si el codigo es cedido se cobra el 100%
                            obj_cedidos = self.env['massive.invoicing.codes.assignment'].search([('company_receives.id', '=', partner_company.id)])
                            cant_prefixes_cedidos = 0
                            prefixes_cedidos = []
                            for cedidos in obj_cedidos:
                                prefixes_cedidos.append(cedidos.prefix)
                            
                            cant_prefixes_cedidos = len(prefixes_cedidos)
                            if cant_prefixes != cant_prefixes_cedidos:
                                unit_fee_value = (unit_fee_value/100)*self.invoicing_companies.percentage_textile_tariff                            
                            
                        else:
                            #Cantidad prefijos = (4Da8D + Peso Fijo + Peso Variable + Mixtos + GLNaGL13) - 1 La Renovación Aportes Patrimoniales Actividades ECR
                            cant_prefixes = (prefixes_company.cant_prefixes_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                            cant_prefixes_cp = (prefixes_company.cant_prefixes_cp_ds+prefixes_company.cant_prefixes_fixed_weight+prefixes_company.cant_prefixes_variable_weight+prefixes_company.cant_prefixes_mixed+prefixes_company.cant_prefixes_gl)
                        #Factura 2: Renovación Prefijos Adicionales (4D a 8D, Peso Fijo y Variable, Mixtos)
                        if cant_prefixes > 0:
                            sale_order_values = {
                                'partner_id' : id_contactP,
                                'client_order_ref' : 'Por pago de la factura antes del 2025-01-31 aplica un descuento por pronto pago del 4.75%',
                                'partner_invoice_id' : id_contactP,
                                'x_origen': 'FM {}'.format(self.year),
                                'x_type_sale': 'Renovación',
                                'x_conditional_discount': (cant_prefixes+prefixes_company.cant_prefixes_gtin)*conditional_discount,
                                'x_conditional_discount_deadline': conditional_discount_deadline,
                                'validity_date' : self.invoicing_companies.expiration_date                            
                            }
                            sale_order = self.env['sale.order'].create(sale_order_values)

                            sale_order_line_values = {
                                'order_id' : sale_order.id,
                                'product_id' : obj_massive_products_padicl.product_id.id,
                                'product_uom_qty' : cant_prefixes, #Cantidad
                                'price_unit' : unit_fee_value,
                                'discount' : discount                            
                            }

                            sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)                            
                        
                            saler_orders_partner.append({'PartnerId':id_contactP,'IdFac2':sale_order.id})
                    
                            process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                            values_update_process = {
                                'invoice_two' : sale_order.id                                              
                            }

                            process_partnersaleorder.update(values_update_process)                            
                    else:
                        continue                   
                if vinculation.name in ('99 Años'):
                    if is_member:
                        continue
                    prefixes_company = obj_company.filtered(lambda pref: pref.partner_id == partner_company)
                    #Cantidad prefijos = Gtin8
                    cant_prefixes = prefixes_company.cant_prefixes_gtin    
                    if cant_prefixes > 0:
                        #Obtener Id Factura 2
                        sale_order_id = 0
                    #Se obtiene el representante ante Logyca al cual quedara asociada la orden de venta
                        id_contactP = 0
                        id_contactPt=0
                        for record in partner_company.child_ids:   
                            ls_contacts = record.x_contact_type
                            for i in ls_contacts:
                                if i.id == 2:
                                    id_contactP = record.id
                                    id_contactPt = partner_company.id
                            
                        if id_contactP == 0:
                            id_contactP = partner_company.id
                            id_contactPt = partner_company

                        sale_order_values = {
                            'partner_id' : id_contactP,
                            'client_order_ref' : 'Por pago de la factura antes del 2025-01-31 aplica un descuento por pronto pago del 4.75%',
                            'partner_invoice_id' : id_contactP,
                            'x_origen': 'FM {}'.format(self.year),
                            'x_type_sale': 'Renovación',
                            'validity_date' : self.invoicing_companies.expiration_date                            
                        }
                        sale_order = self.env['sale.order'].create(sale_order_values)

                        sale_order_line_values = {
                            'order_id' : sale_order.id,
                            'product_id' : obj_massive_products_gtin.product_id.id,
                            'product_uom_qty' : cant_prefixes, #Cantidad
                            'price_unit' : unit_fee_value,
                            'discount' : discount                            
                        }
                        
                        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)       
                        
                        saler_orders_partner.append({'PartnerId':id_contactP,'IdFac2':sale_order.id})
                
                        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].search([('process_id', '=', self.id),('partner_id','=',partner_company.id)])

                        values_update_process = {
                            'invoice_two' : sale_order.id                                              
                        }

                        process_partnersaleorder.update(values_update_process)

    def _create_sale_order_fm(self, vinculation, partner_company, id_contactP, conditional_discount, 
                            conditional_discount_deadline, product_id, product_uom_qty, unit_fee_value, discount, 
                            cant_prefixes_gtin, productgtin):
        #Factura 1: Renovación Prefijo Adicional
        sale_order_values = {
            'partner_id' : id_contactP,
            'client_order_ref' : 'Por pago de la factura antes del 2025-01-31 aplica un descuento por pronto pago del 4.75%',
            'partner_invoice_id' : id_contactP,
            'x_origen': 'FM {}'.format(self.year),
            'x_type_sale': 'Renovación',
            'x_conditional_discount': conditional_discount,
            'x_conditional_discount_deadline': conditional_discount_deadline,
            'validity_date' : self.invoicing_companies.expiration_date                            
        }
        
        sale_order = self.env['sale.order'].create(sale_order_values)
        if product_uom_qty > 0:
            sale_order_line_values = {
                'order_id' : sale_order.id,
                'product_id' : product_id.id,
                'product_uom_qty' : product_uom_qty, #Cantidad
                'price_unit' : unit_fee_value,
                'discount' : discount                            
            }
            
            sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
        if cant_prefixes_gtin > 0:
            if partner_company.fact_annual == 'activos':
                obj_tariff = self.env['massive.invoicing.tariff'].search([('year', '=', self.year),
                                                    ('type_vinculation','=',vinculation.id),
                                                    ('asset_range','=',partner_company.x_asset_range.id),('product_id','=',productgtin.id)])
            else:
                if partner_company.fact_annual == 'ingresos':
                    obj_tariff = self.env['massive.income.tariff'].search([('year', '=', self.year),
                                                    ('type_vinculation','=',vinculation.id),
                                                    ('revenue_range','=',partner_company.x_income_range.id),
                                                    ('product_id','=',productgtin.id)])
            for tariff in obj_tariff:
                fee_value = tariff.unit_fee_value                                                    
            sale_order_line_values_gtin = {
                'order_id' : sale_order.id,
                'product_id' : productgtin.id,
                'product_uom_qty' : cant_prefixes_gtin, #Cantidad
                'price_unit' : fee_value,
                'discount' : discount                            
            }
            
            sale_order_line = self.env['sale.order.line'].create(sale_order_line_values_gtin)

        values_save_process = {
            'process_id' : self.id,
            'partner_id' : partner_company.id,
            'vat' : partner_company.vat,
            'invoice_one' : sale_order.id                                              
        }
        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)        
        return sale_order

    def _create_sale_order_fm_pm(self, partner_company, id_contactP, conditional_discount, 
                            conditional_discount_deadline, product_id, product_uom_qty, unit_fee_value, discount):
        #Factura 1: Renovación Prefijo 
        print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555553')
        sale_order_values = {
            'partner_id' : id_contactP,
            'client_order_ref' : 'Por pago de la factura antes del 2025-01-31 aplica un descuento por pronto pago del 4.75%',
            'partner_invoice_id' : id_contactP,
            'x_origen': 'FM {}'.format(self.year),
            'x_type_sale': 'Renovación',
            'x_conditional_discount': (product_uom_qty)*conditional_discount,
            'x_conditional_discount_deadline': conditional_discount_deadline,
            'validity_date' : self.invoicing_companies.expiration_date                            
        }
        sale_order = self.env['sale.order'].create(sale_order_values)
        assignment_partner_ids = self.env['massive.invoicing.enpointcodeassignment'].search([('process_id', '=', self.id),
                                            ('partner_id','=',partner_company.id),
                                            ('IdEsquema','=',7)])
        print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555554', assignment_partner_ids, id_contactP, self.id)                                            
        cant_pref = True                                     
        for assignment_partner in assignment_partner_ids:
            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555554', assignment_partner)
            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 5555599', cant_pref)
            if assignment_partner.Rango == '4D':
                unit_fee_value = self.env['massive.tariff.prefix'].search([('type_prefix', '=', '4D'),
                                                    ('year','=',self.year)])
            if assignment_partner.Rango == '5D':
                unit_fee_value = self.env['massive.tariff.prefix'].search([('type_prefix', '=', '5D'),
                                                    ('year','=',self.year)])
            if assignment_partner.Rango == '6D':
                unit_fee_value = self.env['massive.tariff.prefix'].search([('type_prefix', '=', '6D'),
                                                    ('year','=',self.year)])
            print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555559', cant_pref)
            if cant_pref:
                print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555557', cant_pref)
                sale_order_line_values = {
                    'order_id' : sale_order.id,
                    'name' : product_id.product_tmpl_id.name + str(assignment_partner.Rango) + ' 60% Descuento',
                    'product_id' : product_id.id,
                    'product_uom_qty' : 1, #Cantidad
                    'price_unit' : (unit_fee_value.fee_value) - (((unit_fee_value.fee_value)*60)/100),
                    'discount' : discount                    
                }
                sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
            else:
                print('EMPRESA PREFIJOS CLIENTE MIEMBROS 555558', product_uom_qty)
                sale_order_line_values = {
                    'order_id' : sale_order.id,
                    'name' : product_id.product_tmpl_id.name + str(assignment_partner.Rango),
                    'product_id' : product_id.id,
                    'product_uom_qty' : product_uom_qty-1, #Cantidad
                    'price_unit' : unit_fee_value.fee_value,
                    'discount' : discount                            
                }
                sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)
            cant_pref = False
        return sale_order
       

    def _create_sale_order_fm_aport(self, partner_company, id_contactP, conditional_discount, 
                            conditional_discount_deadline, product_id, product_uom_qty, unit_fee_value, discount):
        #Factura 1: Renovación Aporte Patrimonial corresponde al producto Renovación Aportes Patrimoniales Actividades ECR
        sale_order_values = {
            'partner_id' : id_contactP,
            'client_order_ref' : 'Por pago de la factura antes del 2025-01-31 aplica un descuento por pronto pago del 4.75%',
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
            'product_id' : product_id.id,
            'product_uom_qty' : product_uom_qty, #Cantidad
            'price_unit' : unit_fee_value,
            'discount' : discount                            
        }
        
        sale_order_line = self.env['sale.order.line'].create(sale_order_line_values)

        values_save_process = {
            'process_id' : self.id,
            'partner_id' : partner_company.id,
            'vat' : partner_company.vat,
            'invoice_one' : sale_order.id                                              
        }
        process_partnersaleorder = self.env['massive.invoicing.partner.saleorder'].create(values_save_process)        
        return True

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

    cant_prefixes_cp_ds = fields.Integer(string='Cant. códigos 4D a 8D Cliente Prefijo', readonly=True)
    prefixes_cp_ds = fields.Char(string='Códigos 4D a 8D', readonly=True)
    
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

