# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


import base64
import io
import requests
import json
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

#---------------------------------- Reporte de inconsistencias Prefijos
class x_MassiveInvoicingPrefixInconsistenciesReport(models.TransientModel):
    _name = 'massive.invoicing.prefix.inconsistencies.report'
    _description = 'Massive Invoicing - Prefix inconsistencies report'
    
    invoicing_companies = fields.Many2one('massive.invoicing.companies', string='Empresas - Ejecución proceso', required=True)
    pdf_file = fields.Binary('PDF file')
    pdf_file_name = fields.Char('PDF name', size=64)
    
    def name_get(self):
        result = []
        for record in self:            
            result.append((record.id, "Reporte de inconsistencias de prefijos - {}".format(record.invoicing_companies.name)))
        return result
    
    #Retonar columnas
    def get_columns(self):
        columns = 'N°,CAMPO,ERROR'
        _columns = columns.split(",")
        return _columns
    
    def get_pdf(self):        
        
        filename= 'PInconsistencias_'+str(self.invoicing_companies.name)+'.pdf'
        pdf = io.BytesIO()
        
        #Encabezado
        def header(canvas, doc):
            canvas.saveState()
            
            #Titulo
            P_one = Paragraph('Reporte de inconsistencias de prefijos',styleN)
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
        data1 = []
        #Encabezado Tabla
        result_columns = self.get_columns()
        data1.append(result_columns)        
        
        #Obtener tipo de proceso
        process_type = self.invoicing_companies.process_type
        if process_type == '1':
            process = False
        else:
            process = True
        #Obtener tipos de vinculación validos
        types_vinculation = []
        obj_type_vinculation_miembros = self.env['logyca.vinculation_types'].search([('name', '=', 'Miembro')])
        obj_type_vinculation_cliente = self.env['logyca.vinculation_types'].search([('name', '=', 'Cliente')])
        for m in obj_type_vinculation_miembros:
            types_vinculation.append(m.id)            
        for c in obj_type_vinculation_cliente:
            types_vinculation.append(c.id)              
        #Obtener lista de Nits
        thirdparties = []
        for partner in self.invoicing_companies.thirdparties:            
            if partner.vat:
                thirdparties.append(partner.vat)
        #Obtener lista de Nits textileros
        textileras = self.env['res.partner'].search([('x_excluded_massive_invoicing','=',False),('x_active_vinculation', '=', True),('x_type_vinculation','in',types_vinculation),('x_sector_id.code','=','10')])
        thirdparties_textil = []
        for partner_textil in textileras:            
            if partner_textil.vat:
                thirdparties_textil.append(partner_textil.vat)
                    
        #Ejecutar API de asignación de codigos
        # body_api = json.dumps({'IsRefact': process, 'Nits': thirdparties})
        body_api = json.dumps({'nit': thirdparties, 'proceso': 'Facturación masiva'})
        headers_api = {'content-type': 'application/json'}
        url_api = self.invoicing_companies.url_enpoint_code_assignment
        payload = {'nit': thirdparties, 'proceso': 'Facturación masiva'}
        response = requests.post(url_api, data=json.dumps(payload))
        result = response.json()
        #raise ValidationError(_(thirdparties_textil))
        
        #Inconsistencias
        inconsistencies = []
        #Recorrer respuesta del api
        thirdparties_api = []
        for data in result["data"]:
            if data['Info Prefijos']:
                partner_vat = data['Nit']
                partner_name = data['Razon social']                    
                for prefijo in data['Info Prefijos']:
                    partner_range = prefijo['Rango descripcion']
                thirdparties_api.append(partner_vat)
            
            #Es textilero
            if partner_vat in thirdparties_textil:
                #Si un textilero no tiene códigos GTIN8, Si la consulta de Wilson en la columna RANGO_PREFIJO trae GTIN8
                if partner_range == 'GTIN8':
                    inconsistencies.append(['GTIN8 en RANGO-PREFIJO','La empresa textilera NIT {}-{} tiene códigos GTIN8.'.format(partner_vat,partner_name)])
                #Si un textilero no tiene códigos de PESO VARIABLE, Si la consulta de Wilson en la columna RANGO_PREFIJO trae %PESO%
                if 'Peso' in partner_range:
                    inconsistencies.append(['Peso en RANGO-PREFIJO','La empresa textilera NIT {}-{} tiene códigos de {}.'.format(partner_vat,partner_name,partner_range)])
            #Si un Miembro o Cliente trae 8D en RANGO-PREFIJO es un error.
            if partner_range not in ['4D','5D','6D','7D','8D','PesoFijo','Peso variable','GTIN8','GLN','GL13']:
                inconsistencies.append(['RANGO-PREFIJO','La empresa NIT {}-{} tiene código {} en RANGO-PREFIJO no permitido.'.format(partner_vat,partner_name,partner_range)])
            
        #raise ValidationError(_(inconsistencies))
        
        #Revisar los clientes y Miembro que NO tienen códigos. Si la api de Asignación de códigos no trae ningun tipo de código es una inconsistencia
        for p in thirdparties:
            if p not in thirdparties_api:
                partner = self.env['res.partner'].search([('vat','=',p),('x_active_vinculation', '=', True)])
                for i in partner:
                    inconsistencies.append(['Código','La empresa NIT {}-{} NO tiene códigos.'.format(i.vat,i.name)])
        
        if not inconsistencies:
            inconsistencies.append([' / ','No se encontraron inconsistencias.'])
            
        #Detalle Tabla 
        num_row = 1
        for i in inconsistencies:
            file = [str(num_row)]
            for row in i: 
                file.append(row)
            num_row = num_row + 1
            data1.append(file)
        
        
        f = Table(data1, repeatRows=1)
        
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
                    'name': 'MassiveInvoicingPrefixInconsistenciesReport',
                    'type': 'ir.actions.act_url',
                    'url': "web/content/?model=massive.invoicing.prefix.inconsistencies.report&id=" + str(self.id) + "&filename_field=pdf_file_name&field=pdf_file&download=true&filename=" + self.pdf_file_name,
                    'target': 'self',
                }
        return action
        
