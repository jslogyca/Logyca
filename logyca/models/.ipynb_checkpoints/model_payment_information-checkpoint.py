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
    partner_id = fields.Many2one('res.partner', string='Tercero', ondelete='restrict')
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
    move_id = fields.Many2one('account.move', string='Factura',readonly=True)
    amount_total = fields.Float(string='Valor recaudado',required = True)
    way_to_pay = fields.Char(string='Código forma de pago', required=True)
    date_payment = fields.Date(string='Fecha de pago')
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Información de pago - {}".format(record.move_id.name)))
        return result
    
    