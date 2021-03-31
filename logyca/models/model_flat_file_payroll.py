# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
    
import xlwt
import base64
import io
import xlsxwriter
import requests
import math
import os
import logging

#---------------------------Modelo para generar REPORTES-------------------------------#

# Archivo Plano Nomina
class FlatFilePayRoll(models.Model):
    _name = 'logyca.flatfile.payroll'
    _description = 'Archivo Plano Nómina'
    
    
    flat_file = fields.Binary('Archivo Plano')
    flat_file_name = fields.Char('Archivo Plano Nombre', size=64)
    date_file = fields.Date(string="Fecha")
    ref = fields.Char(string='Referencia', required=True)
    country_id = fields.Many2one('res.country', string='País')
    description = fields.Char(string='Descripción', required=True)
    journal_id = fields.Many2one('account.journal', string='Diario')    
    type = fields.Char(string='Tipo')
    homologationfile = fields.One2many('logyca.homologationfile.payroll', 'flatfile_id', string = 'Homologación')
    move_id = fields.Many2one('account.move', string='Movimiento',readonly=True)   
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Archivo Plano - {}".format(record.ref)))
        return result
    
    #Leer archivo plano
    def read_file(self):  
        #Leer Archivo
        file_content = base64.decodestring(self.flat_file)
        file_content = file_content.decode("utf-8")
        file_lines = file_content.split("\n")
        
        #Encabezado
        line_one = str(file_lines[0])
        #Se toma como fecha principal la fecha de la primera linea
        date_file = line_one[16:26]
        date_format = '%d/%m/%Y'
        format_date = datetime.strptime(date_file, date_format).strftime(DEFAULT_SERVER_DATE_FORMAT)       
        if not self.date_file:
            self.date_file = format_date
        #Se deja como pais por default colombia
        if not self.country_id:
            self.country_id = 49
        #Diario segun compañia
        company = str(line_one[362:367])
        company = company.rstrip()
        company = company.lstrip()
        company_id = 0
        if company == 'LSER':
            company_id = 1 # Logyca Servicios
        if company == 'IAC' or company == 'GS1':
            company_id = 2 # Logyca Asociacion
        if company == 'LOG':
            company_id = 3 # Logyca Investigación
        journal = self.env['account.journal'].search([('name', 'ilike', 'Nomina'),('company_id','=',company_id)])
        if not self.journal_id:
            self.journal_id = journal.id
        #Tipo
        self.type = line_one[298:310]
        
        #Crear objeto del modelo homologación
        model_homologationfile = self.env['logyca.homologationfile.payroll']
        
        #Eliminar homologacion ya existente
        homologationfile_exists = self.env['logyca.homologationfile.payroll'].search([('flatfile_id', '=', self.id)])
        homologationfile_exists.unlink()
        
        #Detalle
        consecutive = 0
        for line in file_lines:
            #Consecutivo
            consecutive = consecutive + 1
            #Fecha
            date_file = line[16:26]
            date_file = datetime.strptime(date_file, date_format).strftime(DEFAULT_SERVER_DATE_FORMAT)       
            #Referencia
            ref = self.ref
            #Diario
            journal_id = self.journal_id
            #Pais
            country_id = self.country_id
            #Cuenta
            account = str(line[26:35]).rstrip()
            account_code = str(account)
            account = self.env['account.account'].search([('code', '=', account),('company_id','=',company_id)])
            account_id = account.id
            #Descripción
            description = self.description
            #Asociado
            vat = str(line[58:74]).lstrip('0')
            partner = self.env['res.partner'].search([('vat', '=', vat),('x_type_thirdparty','not in',[2])])
            partner_id = 0
            for partner_r in partner:
                partner_id = partner_r.id
            #Grupo Presupuestal
            budget_group = str(line[42:52]).rstrip()
            budget_group_code = budget_group
            budget_group = self.env['logyca.budget_group'].search([('code', '=', budget_group)])
            budget_group_id = budget_group.id            
            #Etiqueta Analitica
            analytic_tag_id = 0
            if company_id == 1:
                analytic_tag_id = budget_group.lser_analytic_tag_ids.id # Logyca Servicios
            if company_id == 2:
                analytic_tag_id = budget_group.iac_analytic_tag_ids.id  # Logyca Asociacion
            if company_id == 3:
                analytic_tag_id = budget_group.log_analytic_tag_ids.id # Logyca Investigación
            #Debito
            amount_debit = str(line[264:279]).lstrip('0')
            if not amount_debit:
                amount_debit = '0'
            decimal_debit = str(line[279:281])
            debit = float(amount_debit+'.'+decimal_debit)
            #Credito
            amount_credit = str(line[281:296]).lstrip('0')
            if not amount_credit:
                amount_credit = '0'
            decimal_credit = str(line[296:298])
            credit = float(amount_credit+'.'+decimal_credit)
            
            #Validaciones
            if not account_id: # Validar cuenta
                raise ValidationError(_('La cuenta '+str(account_code)+' del registro N° '+str(consecutive)+' no existe, por favor verificar.'))    
            if not partner_id: # Validar asociado
                raise ValidationError(_('El asociado con número de identificación '+str(vat)+' del registro N° '+str(consecutive)+' no existe, por favor verificar.'))    
            if account_code[0:1] == '4' or account_code[0:1] == '5' or account_code[0:1] == '6': # Validar grupo presupuestal
                if not budget_group_code:
                    raise ValidationError(_('Las cuentas 4, 5 y 6 deben tener grupo presupuestal verificar registro N° '+str(consecutive)+'.'))    
                if not budget_group:
                    raise ValidationError(_('El grupo presuuestal '+str(budget_group_code)+' del registro N° '+str(consecutive)+' no existe, por favor verificar.'))    
            else:
                if budget_group_code and not budget_group:
                    raise ValidationError(_('El grupo presuuestal '+str(budget_group_code)+' del registro N° '+str(consecutive)+' no existe, por favor verificar.'))                
            
            #Crear Homologación
            if analytic_tag_id != 0:
                model_homologationfile.create({
                    'flatfile_id': self.id,
                    'consecutive': consecutive,
                    'date_file': date_file,
                    'ref': ref,
                    'journal_id': journal_id.id,
                    'country_id': country_id.id,
                    'account_id': account_id,
                    'description': description,
                    'partner_id': partner_id,
                    'budget_group': budget_group_id,
                    'analytic_tag_ids': analytic_tag_id,
                    'debit': debit,
                    'credit': credit,
                })
            else:
                model_homologationfile.create({
                    'flatfile_id': self.id,
                    'consecutive': consecutive,
                    'date_file': date_file,
                    'ref': ref,
                    'journal_id': journal_id.id,
                    'country_id': country_id.id,
                    'account_id': account_id,
                    'description': description,
                    'partner_id': partner_id,
                    'budget_group': budget_group_id,
                    'debit': debit,
                    'credit': credit,
                })
                
    #Crear movimiento contable en estado borrador 
    def create_account_move(self):
        
        if self.move_id:
            raise ValidationError(_('Ya existe un movimiento contable para este archivo, por favor verificar.'))    
        
        homologation = self.env['logyca.homologationfile.payroll'].search([('flatfile_id', '=', self.id)])
        
        cant = 1
        invoice_vals = {}
        for line in homologation:
            if cant == 1:
                #Encabezado account_move
                invoice_vals = {
                    'ref': self.ref,
                    'type': 'entry',
                    'state': 'draft',
                    'date': self.date_file,
                    'company_id': line.company_id.id,
                    'currency_id': line.company_currency_id.id,
                    'invoice_user_id': line.create_uid.id,
                    'team_id': line.create_uid.sale_team_id.id,
                    'journal_id': self.journal_id.id,  
                    'invoice_origin': 'Archivo Plano Nomina',
                    'x_country_account_id': self.country_id.id,
                    'invoice_line_ids': [],
                }
                
            #Detalle account_move_line
            if line.analytic_tag_ids.id:
                move_line = {
                    'ref': self.ref,
                    'name': self.description,                
                    'journal_id': self.journal_id.id,  
                    'company_id': line.company_id.id,
                    'account_id': line.account_id.id,
                    'debit': line.debit,
                    'credit': line.credit,
                    'partner_id': line.partner_id.id,
                    'quantity': 1,
                    'discount': 0,
                    'x_budget_group': line.budget_group.id,
                    'analytic_tag_ids': [(6, 0, [line.analytic_tag_ids.id])],                
                }
            else:
                move_line = {
                    'ref': self.ref,
                    'name': self.description,                
                    'journal_id': self.journal_id.id,  
                    'company_id': line.company_id.id,
                    'account_id': line.account_id.id,
                    'debit': line.debit,
                    'credit': line.credit,
                    'partner_id': line.partner_id.id,
                    'quantity': 1,
                    'discount': 0,
                    'x_budget_group': line.budget_group.id
                }
            
            logging.info("Move Line ==>" + str(move_line))
            logging.info("Invoice Vals ==>" + str(invoice_vals))

            invoice_vals['invoice_line_ids'].append((0, 0, move_line))
            cant = cant + 1
            
        #Insertar en Contabilidad
        move = self.env['account.move'].create(invoice_vals)
        self.move_id = move.id
        
# Homologacion final Archivo Plano Nomina
class HomologationFilePayRoll(models.Model):
    _name = 'logyca.homologationfile.payroll'
    _description = 'Homologacion final Archivo Plano Nómina'
    
    flatfile_id = fields.Many2one('logyca.flatfile.payroll',string='Archivo Plano', required=True, ondelete='cascade')
    consecutive = fields.Integer(string='Consecutivo', required=True)
    date_file = fields.Date(string="Fecha", required=True)
    ref = fields.Char(string='Referencia', required=True)
    journal_id = fields.Many2one('account.journal', string='Diario', required=True)    
    company_id = fields.Many2one(string='Compañia', store=True, readonly=True,related='journal_id.company_id', change_default=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',readonly=True, store=True)
    country_id = fields.Many2one('res.country', string='País', required=True)
    account_id = fields.Many2one('account.account', string='Cuenta', ondelete="restrict", check_company=True)        
    description = fields.Char(string='Descripción', required=True)
    partner_id = fields.Many2one('res.partner', string='Asociado', ondelete='restrict')
    budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta analítica')
    analytic_tag_ids = fields.Many2one('account.analytic.tag', string='Etiqueta analítica')
    debit = fields.Monetary(string='Débito', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Crédito', default=0.0, currency_field='company_currency_id')
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Archivo Plano - ".format(record.ref)))
        return result    

    


    