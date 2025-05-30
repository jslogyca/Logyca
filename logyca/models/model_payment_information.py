# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


# Modelo para guardar las formas de pago con su respectiva parametrizacion contable
class PaymentMethods(models.Model):
    _name = 'logyca.payment.methods'
    _description = 'Formas de pago'
    
    company_id = fields.Many2one('res.company', string='Compañia', required=True)
    way_to_pay = fields.Char(string='Código forma de pago', required=True)
    way_to_pay_description = fields.Char(string='Descripción forma de pago', required=True)
    comision_percentage = fields.Float(string='% Comisión')
    iva_percentage = fields.Float(string='% IVA / Comisión')
    account_comision = fields.Many2one('account.account', string='Cuenta gasto comisión', ondelete="restrict", check_company=True)
    account_iva = fields.Many2one('account.account', string='Cuenta gasto IVA', ondelete="restrict", check_company=True)
    account_convenio = fields.Many2one('account.account', string='Cuenta convenio', ondelete="restrict", check_company=True)
    account_discount = fields.Many2one('account.account', string='Cuenta descuento pronto pago', ondelete="restrict", check_company=True)
    journal_convenio = fields.Many2one('account.journal', string='Diario convenio')    
    partner_id = fields.Many2one('res.partner', string='Tercero Comisión y IVA', ondelete='restrict')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    x_budget_group = fields.Many2one('logyca.budget_group', string='Grupo presupuestal', ondelete='restrict')
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "{}".format(record.way_to_pay_description)))
        return result
    

# Modelo para guardar la información del pago, se llena por el api información enviada por Tienda Virtual
class PaymentInformation(models.Model):
    _name = 'logyca.payment.information'
    _description = 'Información de pago'
    
    partner_id = fields.Many2one('res.partner', string='Cliente', ondelete='restrict', required=True)
    move_name = fields.Char(string='N° Factura', required=True)
    move_id = fields.Many2one('account.move', string='Factura', compute='_account_move_id',readonly=True)
    amount_total = fields.Float(string='Valor recaudado',required = True)
    way_to_pay = fields.Char(string='Código forma de pago', required=True)
    date_payment = fields.Date(string='Fecha de pago')
    payment_completed = fields.Boolean(string='Pago procesado')    
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Información de pago - {}".format(record.move_id.name)))
        return result    
    
    @api.depends('move_name')
    def _account_move_id(self):
        for record in self:
            obj_account_move = self.env['account.move'].search([('name', 'like', record.move_name),('commercial_partner_id.id','=',record.partner_id.id),('state','=','posted')])
            record.move_id = obj_account_move.id
            #for move in obj_account_move:
            #record.move_id = move.id
                
    #Proceso de liquidación de Recaudo
    def create_collection_liquidation(self):
        if self.payment_completed == False:
            #Obtener forma de pago
            obj_payment_method = self.env['logyca.payment.methods'].search([('way_to_pay', '=', self.way_to_pay),('company_id','=',self.move_id.company_id.id)])

            for method in obj_payment_method:
                # -----------------1.Crear Pago
                #Tercero
                #partner_id = 0
                #if method.partner_id:
                #    partner_id = method.partner_id.id
                #else:
                partner_id = self.move_id.commercial_partner_id.id
                #Pago
                payment = {
                    'payment_type': 'inbound',
                    'partner_type' : 'customer',
                    'partner_id': partner_id,
                    'journal_id': method.journal_convenio.id,
                    'payment_method_id': 1, # Manual
                    'amount': self.move_id.amount_residual,
                    'currency_id': self.move_id.currency_id.id,
                    'payment_date': self.date_payment,
                    'communication': self.move_id.name,
                    'invoice_ids': [(6, 0, [self.move_id.id])],
                }
                obj_payment_id = self.env['account.payment'].create(payment)
                move_payment = obj_payment_id.post()
                #Asignar el dato del recibo de pago
                obj_bank = self.env['account.move.line'].search([('payment_id', '=', obj_payment_id.id)], limit=1)
                x_receipt_payment = obj_bank.move_id.name
                self.env['account.move'].search([('id', '=', self.move_id.id)]).write({'x_receipt_payment':x_receipt_payment})                
        else:
            raise ValidationError(_("Pago ya procesado, por favor verificar"))
            
#Pagos
class AccountPayment(models.Model):
    _inherit = 'account.payment'
    x_payment_file = fields.Boolean(string='Reportado en archivo de pago')    
    x_description = fields.Text(string='Descripción')

    def action_read_payments(self):
        self.ensure_one()
        return {
            'name': self.move_id.display_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': self.move_id.id,
        }   
        
    def _prepare_payment_moves(self):
        all_move_vals = super(AccountPayment, self)._prepare_payment_moves()
        all_move_vals_new = []
        #raise ValidationError(_(all_move_vals))
        if len(all_move_vals) == 1:
            for line in all_move_vals:
                #Obtener factura y cliente
                invoice = line.get('ref')
                partner_id = line.get('partner_id')
                #Obtener información de pago
                obj_payment_information = self.env['logyca.payment.information'].search([('move_id.name', '=', invoice),('partner_id.id','=',partner_id),('payment_completed','=',False)])
                if obj_payment_information:
                    #Obtener metodo de pago
                    method = self.env['logyca.payment.methods'].search([('way_to_pay', '=', obj_payment_information.way_to_pay),('company_id','=',obj_payment_information.move_id.company_id.id)])
                    if method:
                        #Modificar lines creadas por el metodo original agregando la logica de comisiones y descuento
                        lines_original = line.get('line_ids')
                        id_debit = 0
                        budget_group = method.x_budget_group.id
                        if method.analytic_account_id:
                            analytic_account = method.analytic_account_id.id
                        else:
                            analytic_account = obj_payment_information.move_id.invoice_line_ids.analytic_account_id.id
                        for move in lines_original:
                            if move[2].get('debit') > 0:
                                line_debit = move[2]
                                #Obtener nombre y valor real pagado
                                name = line_debit.get('name')
                                payment_id = line_debit.get('payment_id')
                                lines = []
                                amount_payment = obj_payment_information.amount_total
                                amount_comision = 0
                                amount_iva = 0
                                #Tiene % Comision
                                if method.comision_percentage > 0:
                                    amount_comision = round((amount_payment*method.comision_percentage)/100,2)
                                    if str(method.account_comision.code).startswith('4') or str(method.account_comision.code).startswith('5')  or str(method.account_comision.code).startswith('6'):
                                        x_budget_group = budget_group
                                        analytic_account_id = analytic_account
                                    else:
                                        x_budget_group = False
                                        analytic_account_id = False
                                        
                                    line_comision = (0,0,{
                                        'payment_id': payment_id,
                                        'name': name,
                                        'currency_id': line_debit.get('currency_id'),
                                        'date_maturity': line_debit.get('date_maturity'),
                                        'partner_id': method.partner_id.id,
                                        'debit': amount_comision,
                                        'account_id': method.account_comision.id,
                                        'x_budget_group': x_budget_group,
                                        'analytic_account_id': analytic_account_id
                                    })
                                    lines.append(line_comision)
                                #Tiene % IVA
                                if method.iva_percentage > 0:
                                    amount_iva = round((((amount_payment*method.comision_percentage)/100)*method.iva_percentage)/100,2)
                                    if str(method.account_iva.code).startswith('4') or str(method.account_iva.code).startswith('5')  or str(method.account_iva.code).startswith('6'):
                                        x_budget_group = budget_group
                                        analytic_account_id = analytic_account
                                    else:
                                        x_budget_group = False
                                        analytic_account_id = False
                                    
                                    line_iva = (0,0,{
                                        'payment_id': payment_id,
                                        'name': name,
                                        'currency_id': line_debit.get('currency_id'),
                                        'date_maturity': line_debit.get('date_maturity'),
                                        'partner_id': method.partner_id.id,
                                        'debit': amount_iva,
                                        'account_id': method.account_iva.id,
                                        'x_budget_group': x_budget_group,
                                        'analytic_account_id': analytic_account_id                        
                                    })
                                    lines.append(line_iva)
                                #Se revisa si el valor pagado contiene descuento
                                if amount_payment == (obj_payment_information.move_id.amount_total-obj_payment_information.move_id.x_value_discounts) and obj_payment_information.move_id.x_value_discounts > 0:
                                    if str(method.account_discount.code).startswith('4') or str(method.account_discount.code).startswith('5')  or str(method.account_discount.code).startswith('6'): 
                                        x_budget_group = budget_group
                                        analytic_account_id = analytic_account
                                    else:
                                        x_budget_group = False
                                        analytic_account_id = False
                                        
                                    line_discount = (0,0,{
                                        'payment_id': payment_id,
                                        'name': name,
                                        'currency_id': line_debit.get('currency_id'),
                                        'date_maturity': line_debit.get('date_maturity'),
                                        'partner_id': line_debit.get('partner_id'),
                                        'debit': obj_payment_information.move_id.x_value_discounts,
                                        'account_id': method.account_discount.id,
                                        'x_budget_group': x_budget_group,
                                        'analytic_account_id': analytic_account_id                        
                                    })
                                    lines.append(line_discount)
                                #Se registra el valor pagado relamente despues de los calculos anteriores
                                if obj_payment_information.move_id.amount_total-amount_comision-amount_iva-obj_payment_information.move_id.x_value_discounts > 0:
                                    if amount_payment == (obj_payment_information.move_id.amount_total-obj_payment_information.move_id.x_value_discounts):
                                        debit_finally = obj_payment_information.move_id.amount_total-amount_comision-amount_iva-obj_payment_information.move_id.x_value_discounts
                                    else:
                                        debit_finally = obj_payment_information.move_id.amount_total-amount_comision-amount_iva
                                    line_payment = (0,0,{
                                        'payment_id': payment_id,
                                        'name': name,
                                        'currency_id': line_debit.get('currency_id'),
                                        'date_maturity': line_debit.get('date_maturity'),
                                        'partner_id': line_debit.get('partner_id'),
                                        'debit': debit_finally,
                                        'account_id': line_debit.get('account_id')                                        
                                    })
                                    lines.append(line_payment)
                                #Se elimina registro existente para ser reemplazado por los anteriores
                                lines_original.pop(id_debit)
                                #Agregar lines a el original
                                for items in lines:
                                    lines_original.append(items)
                                break
                            else:
                                pass
                            
                            id_debit = id_debit + 1
                        
                        #Cambiar valor de line
                        line['line_ids'] = lines_original
                        all_move_vals_new.append(line)
                        #Marcar como pago completado
                        obj_payment_information.write({'payment_completed':True})
        
        #Validar si el pago tiene la cuenta de descuento, en caso de tenerla marcar el check de pago con descuento en la factura
        obj_discount_account = self.env['account.account'].search([('x_discount_account', '=', True)])
        #Retornar movimiento final con los cambios realizados si estos existieron sino retornar el movimiento original
        if len(all_move_vals_new) > 0:
            for line in all_move_vals_new:
                lines = line.get('line_ids')
                obj_move = self.env['account.move'].search([('name', '=', line.get('ref'))])
                for item in lines:
                    if item[2].get('account_id') == obj_discount_account.id:
                        obj_move.write({'x_discount_payment':True})                        
            return all_move_vals_new                
        else:
            #raise ValidationError(_("PAGO POR MODO NORMAL - EN DESARROLLO"))
            for line in all_move_vals:
                lines = line.get('line_ids')
                obj_move = self.env['account.move'].search([('name', '=', line.get('ref'))])
                for item in lines:
                    if item[2].get('account_id') == obj_discount_account.id:
                        obj_move.write({'x_discount_payment':True})
            return all_move_vals
        
        
            