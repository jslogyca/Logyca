# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class x_history_partner_notes(models.Model):
    _name = 'logyca.history_partner_notes'
    _description = 'Información historia de salesforce NOTAS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    
class x_history_partner_emails(models.Model):
    _name = 'logyca.history_partner_emails'
    _description = 'Información historia de salesforce EMAILS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    from_address = fields.Text(string='Desde')    
    to_address = fields.Text(string='Para')    
    cc_Address = fields.Text(string='Cc')    
    bcc_Address = fields.Text(string='Cco')    

class x_history_partner_opportunity(models.Model):
    _name = 'logyca.history_partner_opportunity'
    _description = 'Información historia de salesforce OPORTUNIDADES'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    activity_date = fields.Datetime(string='Fecha creación', required=True)
    name = fields.Char(string='Nombre', size=50, required=True)
    description = fields.Text(string='Descripción') 
    state = fields.Char(string='Estado', size=50, required=True)   
    amount = fields.Integer(string='Monto')
    probability = fields.Integer(string='Probabilidad')
    expected_revenue = fields.Integer(string='Ingresos esperados')
    opportunity_quantity = fields.Integer(string='Cantidad')
    close_date = fields.Datetime(string='Fecha finalización')
    lead_source = fields.Char(string='Origen', size=50, required=True)
    x_history_partner_services = fields.One2many('logyca.history_partner_services', 'opportunity_id', string = 'Servicios')
    x_history_partner_invoices = fields.One2many('logyca.history_partner_invoices', 'opportunity_id', string = 'Facturación')

class x_history_partner_services(models.Model):
    _name = 'logyca.history_partner_services'
    _description = 'Información historia de salesforce SERVICIOS x OPORTUNIDAD'

    opportunity_id = fields.Many2one('logyca.history_partner_opportunity',string='Oportunidad', required=True, ondelete='cascade')
    service = fields.Char(string='Servicio', size=150, required=True)
    service_date = fields.Datetime(string='Fecha')
    quantity = fields.Integer(string='Cantidad')
    unit_price = fields.Integer(string='Precio unitario')
    total_price = fields.Integer(string='Precio total')
    date_initial = fields.Datetime(string='Fecha inicial')
    date_finally = fields.Datetime(string='Fecha final')
    state = fields.Char(string='Estado', size=50)

class x_history_partner_invoices(models.Model):
    _name = 'logyca.history_partner_invoices'
    _description = 'Información historia de salesforce FACTURAS x OPORTUNIDAD'

    opportunity_id = fields.Many2one('logyca.history_partner_opportunity',string='Oportunidad', required=True, ondelete='cascade')
    name = fields.Char(string='Número de solicitud', size=50)
    create_date = fields.Datetime(string='Fecha creación')
    description = fields.Text(string='Concepto')
    condition = fields.Text(string='Condiciones de facturación')
    street_invoice = fields.Text(string='Direccion de facturación')
    state = fields.Char(string='Estado', size=80)
    date_invoice = fields.Datetime(string='Fecha generación factura')
    date_expiration = fields.Datetime(string='Fecha vencimiento')
    num_invoice =  fields.Char(string='Número de factura', size=50)
    comment = fields.Text(string='Observaciones') 
    company = fields.Char(string='Razon social por la que se factura', size=80) 
    phone = fields.Char(string='Telefono', size=50)
    term_payment = fields.Char(string='Nro días acuerdo de pago', size=50)
    responsable = fields.Char(string='Responsable de la factura', size=150) 
    currency = fields.Char(string='Moneda', size=50)
    sector = fields.Char(string='Sector de venta', size=50)
    reason_nc = fields.Text(string='Motivo nota credito') 
    #Productos
    name_service_one = fields.Char(string='Nombre del servicio 1', size=150)
    value_currency_local_one = fields.Integer(string='Valor moneda local servicio 1')
    value_tax_one = fields.Integer(string='Valor impuesto servicio 1')
    month_differs_one = fields.Integer(string='Meses a diferir la factura 1')
    month_initial_differs_one = fields.Char(string='Desde que mes se difiere 1', size=50) 
    name_service_two = fields.Char(string='Nombre del servicio 2', size=150)
    value_currency_local_two = fields.Integer(string='Valor moneda local servicio 2')
    value_tax_two = fields.Integer(string='Valor impuesto servicio 2')
    month_differs_two = fields.Integer(string='Meses a diferir la factura 2')
    month_initial_differs_two = fields.Char(string='Desde que mes se difiere 2', size=50) 
    name_service_three = fields.Char(string='Nombre del servicio 3', size=150)
    value_currency_local_three = fields.Integer(string='Valor moneda local servicio 3')
    value_tax_three = fields.Integer(string='Valor impuesto servicio 3')
    month_differs_three = fields.Integer(string='Meses a diferir la factura 3')
    month_initial_differs_three = fields.Char(string='Desde que mes se difiere 3', size=50) 
    name_service_four = fields.Char(string='Nombre del servicio 4', size=150)
    value_currency_local_four = fields.Integer(string='Valor moneda local servicio 4')
    value_tax_four = fields.Integer(string='Valor impuesto servicio 4')
    month_differs_four = fields.Integer(string='Meses a diferir la factura 4')
    month_initial_differs_four = fields.Char(string='Desde que mes se difiere 4', size=50) 
    
