# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class x_history_partner_notes(models.Model):
    _name = 'logyca.history_partner_notes'
    _description = 'Información historia de salesforce NOTAS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    id_salesforce = fields.Char(string='Id salesforce', size=100)
    title = fields.Text(string='Titulo', required=True)
    activity_date = fields.Datetime(string='Fecha', required=True)
    body = fields.Text(string='Contenido', required=True)    
    
class x_history_partner_emails(models.Model):
    _name = 'logyca.history_partner_emails'
    _description = 'Información historia de salesforce EMAILS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    id_salesforce = fields.Char(string='Id salesforce', size=100)
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
    id_salesforce = fields.Char(string='Id salesforce', size=100)
    activity_date = fields.Datetime(string='Fecha creación', required=True)
    name = fields.Char(string='Nombre', size=50, required=True)
    description = fields.Text(string='Descripción') 
    state = fields.Char(string='Estado', size=50, required=True)   
    amount = fields.Integer(string='Monto')
    probability = fields.Integer(string='Probabilidad')
    expected_revenue = fields.Integer(string='Ingresos esperados')
    opportunity_quantity = fields.Integer(string='Cantidad')
    close_date = fields.Datetime(string='Fecha finalización')
    lead_source = fields.Char(string='Origen', size=50)
    x_history_partner_services = fields.One2many('logyca.history_partner_services', 'opportunity_id', string = 'Servicios')
    x_history_partner_invoices = fields.One2many('logyca.history_partner_invoices', 'opportunity_id', string = 'Facturación')
    attachment_number = fields.Integer('Número de adjuntos', compute='_compute_attachment_number')
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'logyca.history_partner_opportunity'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)   
    
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'logyca.history_partner_opportunity'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'logyca.history_partner_opportunity', 'default_res_id': self.id}
        return res
    

class x_history_partner_services(models.Model):
    _name = 'logyca.history_partner_services'
    _description = 'Información historia de salesforce SERVICIOS x OPORTUNIDAD'

    opportunity_id = fields.Many2one('logyca.history_partner_opportunity',string='Oportunidad', required=True, ondelete='cascade')
    id_salesforce = fields.Char(string='Id salesforce', size=100)
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
    id_salesforce = fields.Char(string='Id salesforce', size=100)
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
    name_contact = fields.Char(string='Contacto', size=150) 
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
    attachment_number = fields.Integer('Número de adjuntos', compute='_compute_attachment_number')
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'logyca.history_partner_invoices'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)
    
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'logyca.history_partner_invoices'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'logyca.history_partner_invoices', 'default_res_id': self.id}
        return res

class x_history_partner_case(models.Model):
    _name = 'logyca.history_partner_case'
    _description = 'Información historia de salesforce CASOS'

    partner_id = fields.Many2one('res.partner',string='Cliente', required=True, ondelete='cascade')
    id_salesforce = fields.Char(string='Id salesforce', size=100)
    case_number = fields.Char(string='Número del caso', size=50)
    contact = fields.Char(string='Contacto', size=200)
    supplied_name = fields.Char(string='Nombre administrado', size=200)
    supplied_email = fields.Char(string='Correo administrado', size=100)
    supplied_phone = fields.Char(string='Telefono administrado', size=100)
    case_type = fields.Char(string='Tipo', size=50)
    case_status = fields.Char(string='Estado', size=50)
    case_origin = fields.Char(string='Origen', size=50)
    subject = fields.Char(string='Titulo', size=500)
    priority = fields.Char(string='Prioridad', size=20)
    description = fields.Text(string='Descripción') 
    is_closed = fields.Boolean(string='Cerrado')
    closed_date = fields.Datetime(string='Fecha finalización')
    owner = fields.Char(string='Propietario', size=200)
    created_date = fields.Datetime(string='Fecha creación')
    created_by = fields.Char(string='Creado por', size=200)
    sla_time = fields.Char(string='Tiempo SLA', size=20)
    support_time = fields.Char(string='Tiempo de soporte', size=20)
    tematic = fields.Char(string='Tematica', size=50)
    support_amount = fields.Char(string='Saldo de soporte', size=20)
    name_client = fields.Char(string='Nombre cliente', size=200)
    origen_form_web = fields.Char(string='Origen del formulario web', size=200)
    nit_client = fields.Char(string='NIT cliente', size=20)
    x_history_partner_casehistory = fields.One2many('logyca.history_partner_casehistory', 'case_id', string = 'Historial')
    attachment_number = fields.Integer('Número de adjuntos', compute='_compute_attachment_number')
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'logyca.history_partner_case'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)   
    
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'logyca.history_partner_case'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'logyca.history_partner_case', 'default_res_id': self.id}
        return res
    
class x_history_partner_casehistory(models.Model):
    _name = 'logyca.history_partner_casehistory'
    _description = 'Información historia de salesforce CASOS HISTORIAL'

    case_id = fields.Many2one('logyca.history_partner_case',string='Caso', required=True, ondelete='cascade')
    id_salesforce = fields.Char(string='Id salesforce', size=100)
    modify_date = fields.Datetime(string='Fecha')
    user = fields.Char(string='Usuario', size=200)
    description = fields.Char(string='Acción', size=500)
    
