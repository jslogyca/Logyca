# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


import base64
import io
import requests
import PyPDF2
#Report Lab - https://www.reportlab.com/docs/reportlab-userguide.pdf
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

try: 
    from reportlab.lib.units import inch, cm
except ImportError:
    cm = None
    
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, SimpleDocTemplate, Table, TableStyle

styles = getSampleStyleSheet()
styleN = styles['Normal']
styleH = styles['Heading1']

#---------------------------------- Reporte de inconsistencias
class x_MassiveInvoicingInconsistenciesReport(models.TransientModel):
    _name = 'massive.invoicing.inconsistencies.report'
    _description = 'Massive Invoicing - Inconsistencies report'
    
    invoicing_companies = fields.Many2one('massive.invoicing.companies', string='Empresas - Ejecución proceso', required=True)
    pdf_file = fields.Binary('PDF file')
    pdf_file_name = fields.Char('PDF name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Reporte de inconsistencias - {}".format(record.invoicing_companies)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'N°,CAMPO,ERROR'
        _columns = columns.split(",")
        return _columns
    
    def get_pdf(self):        
        
        filename= 'Reporte de inconsistencias - '+str(self.invoicing_companies.name)+'.pdf'
        pdf = io.BytesIO()
        
        #Encabezado
        def header(canvas, doc):
            canvas.saveState()
            
            #Titulo
            P_one = Paragraph('Reporte de inconsistencias',styleN)
            w, h = P_one.wrap(doc.width, doc.topMargin)
            P_one.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - h)
            
            P_two = Paragraph(self.invoicing_companies.name,styleN)
            w, h = P_two.wrap(doc.width, doc.topMargin-15)
            P_two.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-15) - h)
            
            #Pagina
            P_pag = Paragraph('Página: '+str(canvas.getPageNumber()),styleN)
            w, h = P_pag.wrap(doc.width+400, doc.topMargin-15)
            P_pag.drawOn(canvas, doc.leftMargin+400, doc.height + (doc.topMargin-15) - h)
            
            #Fecha impresión
            date_today = fields.Date.context_today(self)
            P_date = Paragraph('Fecha impresión: '+str(date_today),styleN)
            w, h = P_date.wrap(doc.width, doc.topMargin-40)
            P_date.drawOn(canvas, doc.leftMargin, doc.height + (doc.topMargin-40) - h)
            
            canvas.restoreState()
            
        doc = BaseDocTemplate(pdf, pagesize=letter,rightMargin=70,leftMargin=70,topMargin=20,bottomMargin=20)
        frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height-2*cm,id='normal')
        template = PageTemplate(id='test', frames=frame, onPage=header)
        doc.addPageTemplates([template])
        elems = []

        #Tabla
        data = []
        #Encabezado Tabla
        result_columns = self.get_columns()
        data.append(result_columns)        
        
        #Inconsistencias
        inconsistencies = []
        for partner in self.invoicing_companies.thirdparties:            
            # 1.Empresa sin rango de Activos
            if not partner.x_asset_range:
                inconsistencies.append(['Rango de activos','La empresa NIT {}-{} no tienen rango de activos'.format(partner.vat,partner.name)])
            # 2.Empresa sin representante ante Logyca o sin conttacto de FE
            cant_contactsP = 0
            cant_contactsFE = 0
            for record in partner.child_ids:   
                ls_contacts = record.x_contact_type
                for i in ls_contacts:
                    if i.id == 2:
                        cant_contactsP = cant_contactsP + 1
                        if not record.name:
                            inconsistencies.append(['Nombre representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca sin nombre.'.format(partner.vat,partner.name)])
                        if record.x_active_for_logyca == False:
                            inconsistencies.append(['Activo representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca inactivo.'.format(partner.vat,partner.name)])
                        if not record.street:
                            inconsistencies.append(['Dirección representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca sin dirección.'.format(partner.vat,partner.name)])
                        if not record.x_city:
                            inconsistencies.append(['Ciudad representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca sin ciudad.'.format(partner.vat,partner.name)])
                        if not record.email:
                            inconsistencies.append(['Email representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca sin email.'.format(partner.vat,partner.name)])
                        if not record.phone and not record.mobile:
                            inconsistencies.append(['Teléfono representante ante Logyca','La empresa NIT {}-{} tiene representante ante Logyca sin teléfono.'.format(partner.vat,partner.name)])
                    if i.id == 3:
                        cant_contactsFE = cant_contactsFE + 1
                        if not record.name:
                            inconsistencies.append(['Nombre contacto FE','La empresa NIT {}-{} tiene contacto FE sin nombre.'.format(partner.vat,partner.name)])
                        if record.x_active_for_logyca == False:
                            inconsistencies.append(['Activo contacto FE','La empresa NIT {}-{} tiene contacto FE inactivo.'.format(partner.vat,partner.name)])
                        if not record.street:
                            inconsistencies.append(['Dirección contacto FE','La empresa NIT {}-{} tiene contacto FE sin dirección.'.format(partner.vat,partner.name)])
                        if not record.x_city:
                            inconsistencies.append(['Ciudad contacto FE','La empresa NIT {}-{} tiene contacto FE sin ciudad.'.format(partner.vat,partner.name)])
                        if not record.email:
                            inconsistencies.append(['Email contacto FE','La empresa NIT {}-{} tiene contacto FE sin email.'.format(partner.vat,partner.name)])
                        if not record.phone and not record.mobile:
                            inconsistencies.append(['Teléfono contacto FE','La empresa NIT {}-{} tiene contacto FE sin teléfono.'.format(partner.vat,partner.name)])
                        
            if cant_contactsP == 0:
                inconsistencies.append(['Representante ante Logyca','La empresa NIT {}-{} no tiene representante ante Logyca.'.format(partner.vat,partner.name)])
            if cant_contactsFE == 0:
                inconsistencies.append(['Contacto FE','La empresa NIT {}-{} no tiene contacto de facturación electronica.'.format(partner.vat,partner.name)])
            if cant_contactsP > 1:
                inconsistencies.append(['Representante ante Logyca','La empresa NIT {}-{} tiene más de un representante ante Logyca.'.format(partner.vat,partner.name)])
            if cant_contactsFE > 1:
                inconsistencies.append(['Contacto FE','La empresa NIT {}-{} tiene más de un contacto de facturación electronica.'.format(partner.vat,partner.name)])
            # 3.Empresas que tiene doble vinculación (Una empresa que es miembro y cliente): Si es posible tener doble vinculación de esta forma (miembro y 99 años) (clientes y 99 años)
            id_miembros = 0
            id_clientes = 0
            obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
            obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])                
            for m in obj_type_vinculation_miembros:                
                id_miembros = m.id
            for c in obj_type_vinculation_cliente:                    
                id_clientes = c.id
            
            cant_Typevinculation = 0
            for record in partner.x_type_vinculation: 
                if record.id == id_miembros or record.id == id_clientes:
                    cant_Typevinculation = cant_Typevinculation + 1
            if cant_Typevinculation > 1:
                inconsistencies.append(['Tipo de vinculación','La empresa NIT {}-{} tiene doble vinculación de tipo miembro y cliente.'.format(partner.vat,partner.name)])
                
        if not inconsistencies:
            inconsistencies.append([' / ','No se encontraron inconsistencias.'])
            
        #Detalle Tabla 
        num_row = 1
        for i in inconsistencies:
            file = [str(num_row)]
            for row in i: 
                file.append(row)
            num_row = num_row + 1
            data.append(file)
        
        
        f = Table(data, repeatRows=1)
        
        styles = TableStyle([
            ('FONTSIZE',(0,0),(-1,-1),7),
            ('FONTSIZE',(0,0),(0,0),8),
            ('TOPPADDING',(0,0),(-1,0),10),
            ('LINEABOVE', (0,0), (-1, 0), 2, colors.black),
        ])
        
        f.setStyle(styles)
        elems.append(f)
        doc.build(elems)
           
        self.write({
            'pdf_file': base64.encodestring(pdf.getvalue()),
            'pdf_file_name': filename,
        })
            
        action = {
                    'name': 'MassiveInvoicingInconsistenciesReport',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=massive.invoicing.inconsistencies.report&id=" + str(self.id) + "&filename_field=pdf_file_name&field=pdf_file&download=true&filename=" + self.pdf_file_name,
                    'target': 'self',
                }
        return action
        
