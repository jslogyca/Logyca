# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from itertools import product
from odoo.exceptions import ValidationError
import xlwt
import base64
import io
import xlsxwriter
import requests
import tempfile
import xlrd

import time
from datetime import datetime, timedelta
import logging

class EpayrollImportFileWizard(models.TransientModel):
    _name = 'epayroll.import.file.wizard'
    _description = 'Cargue Masivo Nominas de Heinshon'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    payslip_batch_id = fields.Many2one('hr.payslip.run', string='payslip batch')
    company_id = fields.Many2one('res.company', string='Company')
    
    def col_position_from_key(self, sheet, key):
        for row_index, col_index in product(range(sheet.nrows), range(sheet.ncols)):
            if sheet.cell(row_index, col_index).value == key:
                return col_index

    def import_file(self):
        employee_rules_list = []
        missing_rules_dict = {}
        rule_row_indexes = [] # indice de las reglas en orden
        rules_found = []
        contract = ""
        
        #listas para capturar personas sin empleado creado o sin tercero
        non_partner_employees, non_employee_employees = ([], ) * 2
        #lista para capturar empleados sin contrato
        non_contract_employees = [] 
        #lista para capturar terceros que están duplicados (cedula encontrada varias veces)
        duplicated_partners = []
        
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno. \n\n Si no es posible cierre este asistente e intente de nuevo.')
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete = False)
            tmp_file.write(base64.b64decode(self and self.file_data or _('Invalid file')))
            tmp_file.close()
            xls_tmp_file = xlrd.open_workbook(tmp_file.name)
        except:
            raise ValidationError('No se puede leer el archivo. Verifique que el formato sea el correcto.')
            return False
        
        sheet = xls_tmp_file.sheet_by_name(xls_tmp_file.sheet_names()[0])
        record_list = [sheet.row_values(i) for i in range(sheet.nrows)]
        
        #paso 1 - Encontrar la columna donde está el número de doc. del colaborador
        employee_identification_loc = self.col_position_from_key(sheet, 'NUMERO DE DOCUMENTO')
        # paso 1.1 - Encontrar la columna donde está el nombre del colaborador
        employee_name_loc = int(self.col_position_from_key(sheet, 'NOMBRE COMPLETO'))
        
        #nombres de columnas
        col_header_names = record_list[4:5]
        
        record_list = record_list[5:] # No tenemos en cuenta el encabezado del archivo

        #paso 2 - iterar los colaboradores para procesar uno a uno
        
            #revisar si existe el colaborador en odoo
              # un empleado está enlazado con un res_user
              # un res_user está enlazado con un partner
        for fila in record_list:
            rule_row_indexes.clear() # limpiamos la lista de indices de reglas
            employee_rules_list.clear()
            rules_found.clear()
            
            #nombre del empleado
            employee_name = fila[employee_name_loc]
            
            # con la identificacion del empleado solamente puedo buscarlo en partners
            partner =self.env['res.partner'].search([('vat','=',str(fila[employee_identification_loc]))])
            
            if len(partner) > 1:
                duplicated_partners.append(employee_name)
                continue
        
            if not partner:
                non_partner_employees.append(employee_name)
            else:
                # con el user encontrado puedo buscarlo en empleados
                employee = self.env['hr.employee'].search([('identification_id','=', str(fila[employee_identification_loc]))])
                if not employee:
                    non_employee_employees.append(employee_name)
                    continue

                #paso 3 - buscar el colaborador basados en su doc. para identificar su contrato activo y el tipo
                # de estructura salarial que le corresponde.
                contract = self.env['hr.contract'].search([('employee_id','=', employee.id),('state','=','open')])
                if not contract:
                    non_contract_employees.append(employee_name)
                    continue

                structure_type = contract.structure_type_id.id

                #paso 4 - buscar la estructura a la que corresponde el tipo de estructura
                #TODO: verificar que el 'tipo de estructura' si tenga una 'estructura' enlazada.
                structure = self.env['hr.payroll.structure'].search([('type_id','=', structure_type)])

                #paso 5 - buscar las reglas de la estructura identificada
                rules = self.env['hr.salary.rule'].search([('struct_id','=', structure.id)])         

                #paso 6 - identificar las columnas de tipo float con ">0"

                    #recorremos la fila de cada empleado buscando las columnas donde el valor sea mayor a cero y
                    #teniendo en cuenta la posición donde lo encontramos
                for index, col in enumerate(fila):
                    payslip_delete = self.env['hr.payslip'].search([('employee_id','=', employee.id),('payslip_run_id','=',self.payslip_batch_id.id)])
                    if payslip_delete:
                        payslip_delete.write({'state': 'draft'})
                        payslip_delete.unlink()
                    if isinstance(col, float) and col > 0.0:
                        #imprimimos ej:Chacon Romero Andrea Katherine-SUELDO - 4550000.0
                        logging.info( employee_name + ' - '+ str(col_header_names[0][index]) +' - '+ str(col))

                        #recorremos las reglas buscando la REFERENCIA de la columna del excel
                        # rules = reglas disponibles en la estructura salarial del empleado en cuestión
                        current_column = str(col_header_names[0][index])

                        for rule in rules:
                            #para cada regla de la estructura, ver si coincide con las reglas identificadas del empl.
                            if rule.x_reference == current_column:
                                employee_rules_list.append(rule)
                                rule_row_indexes.append(index)
                                rules_found.append(rule.x_reference)
                                break

                            #TODO:tener en cuenta mostrar por cada empleado las reglas que no se pudieron encontrar en Odoo.

                            #col_header_names_filtered = [x for x in col_header_names[0] if isinstance(col, float) and col > 0.0]
                            #missing_rules_dict.update({employee_name: (set(col_header_names_filtered) - set(rules_found))})

                #paso 7 - crear la nomina para el empleado
                #vals = {}
                #vals['line_ids'] = {(4, for rec in )}
                payslip_id = self.env['hr.payslip'].create({
                        'name' : str(self.date_from) + '/' + str(self.date_to), 
                        'employee_id': employee.id,
                        'contract_id': contract.id,
                        'struct_id' : structure.id,
                        'date_from': self.date_from,
                        'date_to': self.date_to,
                        'payslip_run_id' : self.payslip_batch_id.id
                    })
                payslip_id._onchange_employee()


                i = 0
                for rule in employee_rules_list:

                    move_line = {
                    'name': rule.x_reference,
                    'code': rule.x_reference,                
                    'category_id': rule.category_id.id,  
                    'quantity': 1,
                    'rate': 100,
                    'salary_rule_id': rule.id,
                    'amount': fila[rule_row_indexes[i]],
                    }

                    logging.info("====> move_line")
                    logging.info(str(move_line))

                    payslip_id.write({'line_ids': [(0, 0, move_line)]})
                    i+=1


                #volver la nómina done
                payslip_id.write({'state' : 'done'})
                
                #crearle un referene a la nomina
                number = payslip_id.number or self.env['ir.sequence'].next_by_code('salary.slip')
                payslip_id.write({'number' : number})
        
        #logging.info("==> rules lists")
        #for rule_item in employee_rules_list:
            #logging.info("===>" + rule_item.name)
        
        # logging.info("==> missing_rules_dict")
        # logging.info(str(missing_rules_dict))
        
        
        logging.info("==> non_contract_employees")
        logging.info(str(non_contract_employees))
        
        logging.info("==> non_employee_employees")
        logging.info(str(non_employee_employees))
        
        return True
