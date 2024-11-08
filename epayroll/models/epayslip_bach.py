# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz

import random
from io import BytesIO
from zipfile import ZipFile
from xml.dom import minidom

import pem, xmlsig, logging
import logging
_logger = logging.getLogger(__name__)

from lxml import etree
from lxml.etree import Element, SubElement
import xml.etree.ElementTree as ET

from pytz import timezone
from six import string_types

from odoo.addons.epayroll.models.epayslip_bach_xml import *
from odoo.addons.epayroll.WSSEDian2.SOAPSing import SOAPSing
from odoo.addons.epayroll.WSSEDian2.Signing import Signing

import pyqrcode

try:
    import pyqrcode
except ImportError:
    _logger.warning('Cannot import pyqrcode library *************************')


try:
    import requests 
except:    
    _logger.warning("no se ha cargado requests")

try:
    import hashlib
except ImportError:
    _logger.warning('Cannot import hashlib library')
    
try:
    from lxml import etree
except:
    print("Cannot import  etree")
    
try:
    import xmltodict
except ImportError:
    _logger.warning('Cannot import xmltodict library')  
    
try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    import OpenSSL
    from OpenSSL import crypto
    type_ = crypto.FILETYPE_PEM
except:
    _logger.warning('Cannot import OpenSSL library')
    
try:
    import base64
except ImportError:
    _logger.warning('Cannot import base64 library ***********************')
    
from random import randint

try:
    import uuid
except ImportError:
    _logger.warning('Cannot import uuid library')
    
try:
    import gzip
except:
    _logger.warning("no se ha cargado gzip ***********************")

import zipfile

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED

class EPayslipBach(models.Model):
    _name = 'epayslip.bach'
    _description = 'EPayslip Bach'
    _inherit = ['mail.thread']


    employee_id = fields.Many2one('hr.employee', string='HR employee')
    contract_id = fields.Many2one('hr.contract', string='HR contract')
    start_date = fields.Date()
    finish_date = fields.Date()
    name = fields.Char(string='Name')  
    payslip_ids = fields.One2many('hr.payslip', 'epayslip_bach_id', string='HR payslip') # agregarle a hr payslip many2one 
    epayslip_line_ids = fields.One2many('epayslip.line', 'epayslip_bach_id', string='Epayslip line')
    state = fields.Selection([('draft', 'Draft'), 
                                ('generated', 'Generated'),
                                ('sent', 'Sent'),
                                ('no_send', 'Not Send'),
                                ('done', 'Done'),
                                ('error', 'With Error'),
                                ('cancel', 'Cancel'),
                                ('cancel_nota', 'Cancel Nota')], default='draft', string='States') 
    epayslip_bach_run_id = fields.Many2one('epayslip.bach.run', string='Epayslip bach run')
    code_cune = fields.Char('CUNE', readonly=True, copy=False)
    date_generate = fields.Datetime('Date Generate')
    total_devengos = fields.Float('Total Devengados', default=0.0)
    total_deducciones = fields.Float('Total Deducciones', default=0.0)
    total_paid = fields.Float('Total Comprobante', default=0.0)
    type_epayroll = fields.Many2one('type.epayroll', string='Tipo de XML utilizado')
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
    number = fields.Char(string='Reference', readonly=True, copy=False)
    qr_payslip = fields.Text(copy=False, string=_('Código QR'), help='Código QR', readonly=True)
    note = fields.Text(copy=False, string='Notes')
    qr_payslip_img = fields.Binary(string=_('Código QR'), help='Código QR')
    xml_document = fields.Text(string='Contenido XML', copy=False)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    filename = fields.Char(string='Nombre del archivo', required=False, readonly=True, states={'draft': [('readonly', False)]})
    filenamexml = fields.Char(string='Nombre del archivo XML', required=False, readonly=True, states={'draft': [('readonly', False)]})
    sequence = fields.Many2one('ir.sequence', string='Sequence')
    number_seq = fields.Integer('Number Seq')
    dian_xml_response = fields.Text(string='DIAN Respuesta', copy=False, readonly=True, states={'NoEnviado': [('readonly', False)]})
    xml_envio = fields.Text(string='XML Env\xc3\xado', required=False, readonly=True, states={'draft': [('readonly', False)]})
    error_ids = fields.One2many('dian.epayslip.bug', 'epayslip_bach_id', string='Errores')
    dian_receipt = fields.Text(string='Mensaje recepci\xc3\xb3n', copy=False, readonly=False, states={'Aceptado': [('readonly', False)], 'Rechazado': [('readonly', False)]})
    dian_message = fields.Text(string='Respuesta env\xc3\xado', copy=False)
    track_id = fields.Char(string='Track ID', required=False, readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    signingtime = fields.Datetime('Fecha y hora firmado', states={'open': [('readonly', True)], 'close': [('readonly', True)]}, help='Date of Invoice with Time Zone', copy=False)
    file_zip = fields.Binary(string='Archivo ZIP')
    epayslip_origin = fields.Many2one('epayslip.bach', string='Epayslip Origin')
    type_note_epayroll = fields.Many2one('type.note.epayroll', string='Epayslip Note Type')
    document_type = fields.Selection(related='type_epayroll.document_type')
    type_note_paysip = fields.Many2one('type.note.epayroll', string='Epayslip Note Type')
    epayslip_origin = fields.Many2one('epayslip.bach', string='Epayslip Origin')

    @api.model
    def _get_date_invoice_tz(self):
        formato = '%Y-%m-%d %H:%M:%S'
        tz = pytz.timezone('America/Bogota')
        fecha_envio = datetime.now(tz).strftime(formato)
        now = datetime.now()
        return now

    def action_generated_number(self, epayslip):
        if epayslip.document_type == 'payslip':
            sequence_id = self.env.ref('epayroll.seq_epayslip_slip')
            number = self.env['ir.sequence'].next_by_code('bach.epayslip')
            number_seq = number[2:len(number)]
        else:
            sequence_id = self.env.ref('epayroll.seq_epayslip_note')
            number = self.env['ir.sequence'].next_by_code('bachepayslipnote')
            number_seq = number[3:len(number)]
        return epayslip.write({'number': number, 'sequence': sequence_id.id, 'number_seq': int(number_seq)})

    def get_value_etotal(self, tag, type, epayslip_bach_id):
        self._cr.execute(''' SELECT sum(value)
                                FROM epayslip_line l
                                INNER JOIN hr_electronictag_structure e ON e.id=l.electronictag_id
                                WHERE e.ref not in (%s) AND e.type=%s AND epayslip_bach_id=%s ''', (tag, type, epayslip_bach_id.id))
        value_tag = self._cr.fetchone()
        if value_tag and value_tag[0]:
            return value_tag[0]
        else:
            return 0.0

    def get_value_cant_epayslip(self, employee_id, start_date, finish_date, rule):
        self._cr.execute(''' SELECT sum(d.number_of_days)
                                FROM hr_payslip_worked_days d
                                INNER JOIN hr_work_entry_type td on td.id = d.work_entry_type_id
                                INNER JOIN hr_payslip p on p.id=d.payslip_id
                                WHERE p.id in (select id from hr_payslip where employee_id=%s and date_from>=%s and date_from<=%s)
                                AND td.code = %s and p.state='done' ''', (employee_id.id, start_date, finish_date, rule))
        value_tag = self._cr.fetchone()
        if value_tag and value_tag[0]:
            return value_tag[0]
        else:
            return 0.0

    def get_value_cant_epayslip_incap(self, employee_id, start_date, finish_date):
        self._cr.execute(''' SELECT sum(d.number_of_days)
                                FROM hr_payslip_worked_days d
                                INNER JOIN hr_payslip p on p.id=d.payslip_id
                                INNER JOIN hr_work_entry_type td on td.id = d.work_entry_type_id
                                WHERE p.id in (select id from hr_payslip where employee_id=%s and date_from>=%s and date_from<=%s)
                                AND td.code in ('INCAPACIDAD_PRORROGA', 'INCAPACIDAD_INICIAL', 'INCAPACIDAD_ARL') 
                                and p.state='done' ''', (employee_id.id, start_date, finish_date))
        value_tag = self._cr.fetchone()
        if value_tag and value_tag[0]:
            return value_tag[0]
        else:
            return 0.0

    def generate_cune(self):
        for epayslip in self:
            # NumNE = epayslip.sequence # Numero de Documento Soporte de Pago de Nómina Electronica. (Prefijo concatenado con el Consecutivo de la nómina)
            NumNE = (self.sequence.prefix) + str(self.number_seq)
            if epayslip.date_generate:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                fecha_envio = epayslip.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
                print('CUNE ********** FECHA 2222222', fecha_envio)
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                print('CUNE ********** FECHA 2222222', FecNE)

            # FecNE = fecha_envio
            # HorNE = fecha_envio
            # HorNE = epayslip.hour_generate # Hora de Generación del Documento incluyendo GMT.
            # HorNE = '10:53:10-05:00' # Hora de Generación del Documento incluyendo GMT.
            # ValDev = epayslip.total_devengos # Total Devengos, con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            ValDev = round(self.get_value_etotal('DevengadosTotal', 'devengados', self),3) # Total Devengos, con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', str('%.2f' % round(abs(ValDev), 2)))
            ValDed = round(self.get_value_etotal('DeduccionesTotal', 'deducciones', self),3)  # Total Deducciones, con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', ValDed)
            ValTolNE = round((ValDev - ValDed), 3)  # Total Pagado (Devengado - Deducciones), con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', ValTolNE)
            NitNE = epayslip.company_id.partner_id.vat # NIT del Emisor del Documento, sin puntos ni guiones, sin digito de verificación.
            DocEmp = epayslip.employee_id.identification_id # Número de Identificación del Empleado, sin puntos ni guiones, sin digito de verificación.
            TipoXML = epayslip.type_epayroll.code # Tipo de XML utilizado.
            SoftwarePin = epayslip.company_id.connection_payslip_id.pin_software # Pin del Software utilizado.
            TipAmb = epayslip.company_id.connection_payslip_id.type # Número de identificación del ambiente utilizado por el contribuyente para emitir la nómina, validar el numeral 5.1.1.
            if not TipAmb:
                raise ValidationError(u'Debe configurar el ambiente de la DIAN en la company')
            print ('/////////', NumNE, FecNE, str(str('%.2f' % round(abs(ValDev), 2))), str(str('%.2f' % round(abs(ValDev-ValTolNE), 2))), str(str('%.2f' % round(abs(ValTolNE), 2))), NitNE, DocEmp, TipoXML, SoftwarePin, TipAmb)
            cune = NumNE + FecNE + str(str('%.2f' % round(abs(ValDev), 2))) + str(str('%.2f' % round(abs(ValDev-ValTolNE), 2))) + str(str('%.2f' % round(abs(ValTolNE), 2))) + NitNE + DocEmp + TipoXML + SoftwarePin + TipAmb
            print('CUNE **********', cune)
            return cune
        return

    def generate_cune_note(self):
        for epayslip in self:
            NumNE = (self.sequence.prefix) + str(self.number_seq)
            if epayslip.date_generate:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                print('CUNE ********** FECHA 1111', epayslip.date_generate)
                fecha_envio = epayslip.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
                print('CUNE ********** FECHA 2222222', fecha_envio)
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                print('CUNE ********** FECHA 2222222', FecNE)

            if self.type_note_paysip.code == '2':
                ValDev = 0.0
            else:
                ValDev = round(self.get_value_etotal('DevengadosTotal', 'devengados', self),3) # Total Devengos, con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', str('%.2f' % round(abs(ValDev), 2)))
            if self.type_note_paysip.code == '2':
                ValDed = 0.0
            else:
                ValDed = round(self.get_value_etotal('DevengadosTotal', 'devengados', self),3)  # Total Deducciones, con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', ValDed)
            if self.type_note_paysip.code == '2':
                ValTolNE = 0.0
            else:
                ValTolNE = round((ValDev - ValDed), 3)  # Total Pagado (Devengado - Deducciones), con punto decimal, con decimales truncados a dos (2) dígitos, sin separadores de miles, ni símbolo pesos.
            print('CUNE **********', ValTolNE)
            NitNE = epayslip.company_id.partner_id.vat # NIT del Emisor del Documento, sin puntos ni guiones, sin digito de verificación.
            if self.type_note_paysip.code == '2':
                DocEmp = '0'
            else:
                DocEmp = epayslip.employee_id.identification_id # Número de Identificación del Empleado, sin puntos ni guiones, sin digito de verificación.

            TipoXML = epayslip.type_epayroll.code # Tipo de XML utilizado.
            SoftwarePin = epayslip.company_id.connection_payslip_id.pin_software # Pin del Software utilizado.
            TipAmb = epayslip.company_id.connection_payslip_id.type # Número de identificación del ambiente utilizado por el contribuyente para emitir la nómina, validar el numeral 5.1.1.

            if not TipAmb:
                raise ValidationError(u'Debe configurar el ambiente de la DIAN en la company')
            cune = NumNE + FecNE + str(str('%.2f' % round(abs(ValDev), 2))) + str(str('%.2f' % round(abs(ValDev-ValTolNE), 2))) + str(str('%.2f' % round(abs(ValTolNE), 2))) + NitNE + DocEmp + TipoXML + SoftwarePin + TipAmb
            print('CUNE AJUSTE **********', cune)
            return cune
        return

    def get_cune(self):
        if self.document_type == 'payslip':
            cune = self.generate_cune()
        else:
            cune = self.generate_cune_note()

        if cune == None:
            return
        else:
            # sha384 = hashlib.sha384(cune.encode('utf-8'))
            sha384 = hashlib.new("sha384", cune.encode('utf8'))
            cune_vr = sha384.hexdigest()
            self.write({'code_cune': cune_vr})
            print('CUNE CODIFI **********',cune_vr)
            return cune_vr

    def _get_barcode_img(self):
        for epayslip in self:
            cune = epayslip.code_cune
            NumNIE = epayslip.number
            if epayslip.date_generate:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                print('CUNE ********** FECHA 1111', epayslip.date_generate)
                fecha_envio = epayslip.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                FecNIE = FecNE[0:10]
                HorNIE = FecNE[10:24]
            else:
                FecNIE = ''
            print('FECHA BARCODE', FecNIE, HorNIE, FecNE)
            NitNIE = epayslip.company_id.partner_id.vat or ''
            DocEmp = epayslip.employee_id.identification_id or ''
            ValDev = self.get_value_etotal('DevengadosTotal', 'devengados', self)
            ValDev = str('%.2f' % round(ValDev, 2))
            ValDed = self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
            ValDed = str('%.2f' % round(ValDed, 2))
            ValTol = self.get_value_etotal('DevengadosTotal', 'devengados', self) - self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
            ValTol = str('%.2f' % round(ValTol, 2))

            if cune == None:
                cune = ''
            print('CODIGO QR ****************')
            print('NumNIE', NumNIE)
            print('FecNIE', FecNIE)
            print('HorNIE', HorNIE)
            print('NitNIE', NitNIE)
            print('DocEmp', HorNIE)
            print('ValDev', ValDev)
            print('ValDed', ValDed)
            print('ValTol', ValTol)
            if epayslip.company_id.connection_payslip_id.type == '1':
                texto = 'NumNIE:' + NumNIE + '                 FecNIE=' + FecNIE + '                 HorNIE=' + HorNIE + '                 NitNIE=' + NitNIE + '                 DocEmp=' + DocEmp + '                 ValDev=' + ValDev + '                 ValDed=' + ValDed +                  '                 ValTol=' + ValTol +    '                 CUNE=' + cune + '                 URL=https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + cune
            else:
                texto = 'NumNIE:' + NumNIE + '                 FecNIE=' + FecNIE + '                 HorNIE=' + HorNIE + '                 NitNIE=' + NitNIE + '                 DocEmp=' + DocEmp + '                 ValDev=' + ValDev + '                 ValDed=' + ValDed +                  '                 ValTol=' + ValTol +    '                 CUNE=' + cune + '                 URL=https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + cune
            qr_code = pyqrcode.create(texto)
            epayslip.write({'qr_payslip': texto})
            print('BARCODE TEXTO', texto)
            img_as_str = qr_code.png_as_base64_str(scale=5)
            epayslip.qr_payslip_img = img_as_str
        return

    def _get_barcode_img_note(self):
        for epayslip in self:
            cune = epayslip.code_cune
            NumNIE = epayslip.number
            if epayslip.date_generate:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                print('CUNE ********** FECHA 1111', epayslip.date_generate)
                fecha_envio = epayslip.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                FecNIE = FecNE[0:10]
                HorNIE = FecNE[10:24]
            else:
                FecNIE = ''
            TipoNota = self.type_note_paysip.code or ''
            NitNIE = epayslip.company_id.partner_id.vat or ''
            if self.type_note_paysip.code == '2':
                DocEmp = '0'
                ValDev = '0'
                ValDed = '0'
                ValTol = '0'
            else:            
                DocEmp = epayslip.employee_id.identification_id or ''
                ValDev = self.get_value_etotal('DevengadosTotal', 'devengados', self)
                ValDev = str('%.2f' % round(ValDev, 2))
                ValDed = self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
                ValDed = str('%.2f' % round(ValDed, 2))
                ValTol = self.get_value_etotal('DevengadosTotal', 'devengados', self) - self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
                ValTol = str('%.2f' % round(ValTol, 2))

            if cune == None:
                cune = ''
            if epayslip.company_id.connection_payslip_id.type == '1':
                texto = 'NumNIE:' + NumNIE + '                 FecNIE=' + FecNIE + '                 HorNIE=' + HorNIE + '                 TipoNota=' + TipoNota + '                 NitNIE=' + NitNIE + '                 DocEmp=' + DocEmp + '                 ValDev=' + ValDev + '                 ValDed=' + ValDed +                  '                 ValTol=' + ValTol +    '                 CUNE=' + cune + '                 URL=https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + cune
            else:
                texto = 'NumNIE:' + NumNIE + '                 FecNIE=' + FecNIE + '                 HorNIE=' + HorNIE + '                 TipoNota=' + TipoNota + '                 NitNIE=' + NitNIE + '                 DocEmp=' + DocEmp + '                 ValDev=' + ValDev + '                 ValDed=' + ValDed +                  '                 ValTol=' + ValTol +    '                 CUNE=' + cune + '                 URL=https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + cune
            qr_code = pyqrcode.create(texto)
            epayslip.write({'qr_payslip': texto})
            img_as_str = qr_code.png_as_base64_str(scale=5)
            epayslip.qr_payslip_img = img_as_str
        return        

    def get_payslip_period(self, employee_id, date_start, date_stop, epayslip):
        payslip_ids = self.env['hr.payslip'].search([('employee_id','=',employee_id.id),('state','=','done'),('date_from','>=',date_start),
                                                        ('date_from','<=',date_stop)])
        if payslip_ids:
            lista = []
            for payslip_id in payslip_ids:
                lista.append((4,payslip_id.id))
            self.payslip_ids = lista
        return

    def update_tabla(self, epayslip):
        lista = []
        if len(self.payslip_ids) == 0:
            return
        consulta=""" 
                SELECT r.id as rule, ep.id, sum(abs(l.total)) as total, """+str(epayslip.id)+""" as batch_id, 
                l.employee_id, 
                """+str(epayslip.epayslip_bach_run_id.id)+""" as batch_run_id, ep.name
                from hr_payslip_line l
                inner join hr_salary_rule r on r.id=l.salary_rule_id
                inner join hr_electronictag_structure ep on ep.id=r.electronictag_id
                where slip_id in %s and total <> 0.0  group by r.id, ep.id, l.employee_id""" 
        self.env.cr.execute(consulta,(tuple(epayslip.payslip_ids.ids),))
        datos = self.env.cr.dictfetchall()
        for d in datos:
            dic = {}
            dic['salary_rule_id'] = d['rule']
            dic['electronictag_id'] = d['id']
            dic['value'] = d['total']
            dic['epayslip_bach_id'] = d['batch_id']
            dic['employee_id'] = d['employee_id']
            dic['bach_run_id'] = d['batch_run_id']
            dic['name'] = d['name']
            lista.append((0,0,dic))
        if len(lista)>0:
            epayslip.epayslip_line_ids.unlink()
            epayslip.epayslip_line_ids = lista
        return True

    # def update_tabla(self, epayslip):
    #     lista = []
    #     if len(self.payslip_ids) == 0:
    #         return
    #     consulta=""" 
    #             SELECT ep.id, sum(abs(l.total)) as total, """+str(epayslip.id)+""" as batch_id, l.employee_id, """+str(epayslip.epayslip_bach_run_id.id)+""" as batch_run_id, ep.name,

    #             from hr_payslip_line l
    #             inner join hr_salary_rule r on r.id=l.salary_rule_id
    #             inner join hr_electronictag_structure ep on ep.id=r.electronictag_id
    #             where slip_id in %s and total <> 0.0  group by ep.id, 3, l.employee_id, 5, 6""" 
    #     self.env.cr.execute(consulta,(tuple(epayslip.payslip_ids.ids),))
    #     datos = self.env.cr.dictfetchall()
    #     for d in datos:
    #         dic = {}
    #         dic['salary_rule_id'] = False
    #         dic['electronictag_id'] = d['id']
    #         dic['value'] = d['total']
    #         dic['epayslip_bach_id'] = d['batch_id']
    #         dic['employee_id'] = d['employee_id']
    #         dic['bach_run_id'] = d['batch_run_id']
    #         dic['name'] = d['name']
    #         lista.append((0,0,dic))
    #     if len(lista)>0:
    #         epayslip.epayslip_line_ids.unlink()
    #         epayslip.epayslip_line_ids = lista
    #     return True

    def get_epayslip_line(self, epayslip):
        self.update_tabla(epayslip)
        self.env.cr.commit()

    def update_total(self):
        DevengadosTotal = self.get_value_etotal('DevengadosTotal', 'devengados', self)
        self.total_devengos = round(DevengadosTotal, 2)
        DeduccionesTotal = self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
        self.total_deducciones = round(DeduccionesTotal, 2)
        ComprobanteTotal = DevengadosTotal - DeduccionesTotal
        self.total_paid = round(ComprobanteTotal, 2)
        self.note = self.number + ' - ' + self.employee_id.name
        for line in self.epayslip_line_ids:
            if line.electronictag_id.id == 33:
                line.value = DevengadosTotal
            else:
                continue

    def update_data(self):
        for epayslip in self:
            epayslip.date_generate = self._get_date_invoice_tz()
            epayslip.action_generated_number(epayslip)
            epayslip.get_cune()
            epayslip._get_barcode_img()
            epayslip.get_payslip_period(epayslip.employee_id, epayslip.start_date, epayslip.finish_date, epayslip)
            epayslip.get_epayslip_line(epayslip)
            epayslip.update_total()
            self.env.cr.commit()
            return epayslip.write({'state': 'generated'})

    def action_cancel(self): 
        return self.write({'state': 'cancel'})

    def action_draft(self):
        self._cr.execute(''' DELETE FROM dian_epayslip_bug WHERE epayslip_bach_id = %s''', (self.id,))
        self._cr.execute(''' DELETE FROM epayslip_line WHERE epayslip_bach_id = %s''', (self.id,))
        return self.write({'state': 'draft', 'xml_document': None, 'dian_receipt': None, 'track_id': None,
                                'code_cune': None, 'total_devengos': 0.0, 'total_deducciones': 0.0, 'total_paid': 0.0})

    def firmar_facturae(self, xml_facturae):

        def _sign_file(cert, password, request):
            min = 1
            max = 99999
            signature_id = 'xmldsig-88fbfc45-3be2-4c4a-83ac-0796e1bad4c5'
            signed_properties_id = 'xmldsig-88fbfc45-3be2-4c4a-83ac-0796e1bad4c5-signedprops'
            key_info_id = 'xmldsig-88fbfc45-3be2-4c4a-83ac-0796e1bad4c5-keyinfo'
            reference_id = 'xmldsig-88fbfc45-3be2-4c4a-83ac-0796e1bad4c5-ref0'
            object_id = 'Object%05d' % random.randint(min, max)
            xades = 'http://uri.etsi.org/01903/v1.3.2#'
            algoritm = 'http://www.w3.org/2001/04/xmlenc#sha256'
            sig_policy_identifier = 'https://facturaelectronica.dian.gov.co/politicadefirma/v2/politicadefirmav2.pdf'
            sig_policy_hash_value = 'dMoMvtcG5aIzgYo0tIsSQeVJBDnUnfSOfBpxXrmor0Y='
            root = etree.fromstring(request.encode('utf-8'))
            sign = xmlsig.template.create(c14n_method=xmlsig.constants.TransformInclC14N, sign_method=xmlsig.constants.TransformRsaSha256, name=signature_id, ns='ds')
            key_info = xmlsig.template.ensure_key_info(sign, name=key_info_id)
            x509_data = xmlsig.template.add_x509_data(key_info)
            xmlsig.template.x509_data_add_certificate(x509_data)
            p12 = crypto.load_pkcs12(base64.decodestring(self.company_id.connection_payslip_id.certificate_id.cert_file), self.company_id.connection_payslip_id.certificate_id.cert_pass)
            priv_key = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
            certificate1 = p12.get_certificate()
            certificate1_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
            ref = xmlsig.template.add_reference(sign, xmlsig.constants.TransformSha256, name=reference_id, uri=None)
            xmlsig.template.add_reference(sign, xmlsig.constants.TransformSha256, uri='#' + key_info_id)
            xmlsig.template.add_reference(sign, xmlsig.constants.TransformSha256, uri='#' + signed_properties_id, uri_type='http://uri.etsi.org/01903#SignedProperties')
            xmlsig.template.add_transform(ref, xmlsig.constants.TransformEnveloped)
            object_node = etree.SubElement(sign, etree.QName(xmlsig.constants.DSigNs, 'Object'))
            qualifying_properties = etree.SubElement(object_node, etree.QName(xades, 'QualifyingProperties'), nsmap={'xades': xades, 'xades141': 'http://uri.etsi.org/01903/v1.4.1#'}, attrib={'Target': '#' + signature_id})
            signed_properties = etree.SubElement(qualifying_properties, etree.QName(xades, 'SignedProperties'), attrib={'Id': signed_properties_id})
            signed_signature_properties = etree.SubElement(signed_properties, etree.QName(xades, 'SignedSignatureProperties'))
            now = datetime.now()
            fecha_actual = now.isoformat()
            formato = '%Y-%m-%dT%H:%M:%S'
            tz = pytz.timezone('America/Bogota')
            fecha_envio = datetime.now(tz).strftime(formato)
            fecha_envio = fecha_envio + '-05:00'
            # self.write({'signingtime': fecha_actual})
            etree.SubElement(signed_signature_properties, etree.QName(xades, 'SigningTime')).text = fecha_envio
            signing_certificate = etree.SubElement(signed_signature_properties, etree.QName(xades, 'SigningCertificate'))
            signing_certificate_cert1 = etree.SubElement(signing_certificate, etree.QName(xades, 'Cert'))
            cert_digest1 = etree.SubElement(signing_certificate_cert1, etree.QName(xades, 'CertDigest'))
            etree.SubElement(cert_digest1, etree.QName(xmlsig.constants.DSigNs, 'DigestMethod'), attrib={'Algorithm': algoritm})
            hash_cert1 = hashlib.sha256(crypto.dump_certificate(crypto.FILETYPE_ASN1, certificate1))
            etree.SubElement(cert_digest1, etree.QName(xmlsig.constants.DSigNs, 'DigestValue')).text = base64.b64encode(hash_cert1.digest())
            issuer_serial1 = etree.SubElement(signing_certificate_cert1, etree.QName(xades, 'IssuerSerial'))
            etree.SubElement(issuer_serial1, etree.QName(xmlsig.constants.DSigNs, 'X509IssuerName')).text = 'C=CO,L=Bogota D.C.,O=Andes SCD.,OU=Division de certificacion entidad final,CN=CA ANDES SCD S.A. Clase II,1.2.840.113549.1.9.1=#1614696e666f40616e6465737363642e636f6d2e636f'
            etree.SubElement(issuer_serial1, etree.QName(xmlsig.constants.DSigNs, 'X509SerialNumber')).text = str(certificate1.get_serial_number())
            signature_policy_identifier = etree.SubElement(signed_signature_properties, etree.QName(xades, 'SignaturePolicyIdentifier'))
            signature_policy_id = etree.SubElement(signature_policy_identifier, etree.QName(xades, 'SignaturePolicyId'))
            sig_policy_id = etree.SubElement(signature_policy_id, etree.QName(xades, 'SigPolicyId'))
            etree.SubElement(sig_policy_id, etree.QName(xades, 'Identifier')).text = sig_policy_identifier
            sig_policy_hash = etree.SubElement(signature_policy_id, etree.QName(xades, 'SigPolicyHash'))
            etree.SubElement(sig_policy_hash, etree.QName(xmlsig.constants.DSigNs, 'DigestMethod'), attrib={'Algorithm': algoritm})
            hash_value = sig_policy_hash_value
            etree.SubElement(sig_policy_hash, etree.QName(xmlsig.constants.DSigNs, 'DigestValue')).text = hash_value
            signer_role = etree.SubElement(signed_signature_properties, etree.QName(xades, 'SignerRole'))
            claimed_roles = etree.SubElement(signer_role, etree.QName(xades, 'ClaimedRoles'))
            etree.SubElement(claimed_roles, etree.QName(xades, 'ClaimedRole')).text = 'third party'
            ctx = xmlsig.SignatureContext()
            ctx.x509 = p12.get_certificate().to_cryptography()
            ctx.public_key = ctx.x509.public_key()
            ctx.private_key = p12.get_privatekey().to_cryptography_key()
            root.append(sign)
            uri_tag = True
            for e in root.iter():
                if e.tag == '{http://www.w3.org/2000/09/xmldsig#}SignatureValue':
                    e.set('Id', 'xmldsig-88fbfc45-3be2-4c4a-83ac-0796e1bad4c5-sigvalue')
                if uri_tag and e.tag == '{http://www.w3.org/2000/09/xmldsig#}Reference':
                    e.set('URI', '')
                    uri_tag = False

            ctx.sign(sign)
            res = ctx.verify(sign)
            return root

        tree = etree.fromstring(xml_facturae.encode('utf-8'), etree.XMLParser(remove_blank_text=True, encoding='utf-8'))
        xml_facturae = etree.tostring(tree, xml_declaration=False, encoding='UTF-8').decode('utf8')
        cert = self.company_id.connection_payslip_id.certificate_id.cert_file
        cert_password = self.company_id.connection_payslip_id.certificate_id.cert_pass
        invoice_root = _sign_file(cert, cert_password, xml_facturae)
        invoice_signed = etree.tostring(invoice_root, xml_declaration=False, encoding='UTF-8').decode('utf8')
        invoice_signed = invoice_signed.replace('xmlns="urn:dian:gov:co:facturaelectronica:NominaIndividual"', 'xmlns="dian:gov:co:facturaelectronica:NominaIndividual"')
        signature = xmlstr = invoice_signed[invoice_signed.find('<ds:Signature'):invoice_signed.find('</ds:Signature>') + 15]
        invoice_signed = invoice_signed.replace(signature, '')
        invoice_signed = invoice_signed.replace('<ext:ExtensionContent/>', '<ext:ExtensionContent>' + signature + '</ext:ExtensionContent>')
        return invoice_signed

    def _ssc(self):
        return hashlib.new('sha384', (str(self.company_id.connection_payslip_id.software_code) + str(self.company_id.connection_payslip_id.pin_software) + (self.sequence.prefix) + str(self.number_seq)).encode('utf-8')).hexdigest()

    def get_value_reg(self, tag, epayslip_bach_id):
        self._cr.execute(''' SELECT value
                                FROM epayslip_line l
                                INNER JOIN hr_electronictag_structure e ON e.id=l.electronictag_id
                                WHERE e.ref=%s AND epayslip_bach_id=%s ''', (tag, epayslip_bach_id.id))
        value_tag = self._cr.fetchone()
        if value_tag and value_tag[0]:
            return value_tag[0]
        else:
            return 0.0

    def get_value_reg_type(self, tag, epayslip_bach_id, type):
        self._cr.execute(''' SELECT value
                                FROM epayslip_line l
                                INNER JOIN hr_electronictag_structure e ON e.id=l.electronictag_id
                                WHERE e.ref=%s AND epayslip_bach_id=%s AND e.type = %s''', (tag, epayslip_bach_id.id, type))
        value_tag = self._cr.fetchone()
        if value_tag and value_tag[0]:
            return value_tag[0]
        else:
            return 0.0

    def generate_payslip_xml(self):
        self.get_cune()
        self._get_barcode_img()
        formato = '%Y-%m-%d %H:%M:%S'
        tz = pytz.timezone('America/Bogota')
        print('CUNE ********** FECHA 1111', self.date_generate)
        fecha_envio = self.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
        FecNE = fecha_envio.replace(' ', '') + '-05:00'
        FecNIE = FecNE[0:10]
        HorNIE = FecNE[10:24]
        NominaIndividual = Element('NominaIndividual', 
            attrib={'xmlns': 'urn:dian:gov:co:facturaelectronica:NominaIndividual',
            'SchemaLocation': '',
            'xsi__schemaLocation': 'dian:gov:co:facturaelectronica:NominaIndividual NominaIndividualElectronicaXSD.xsd',
            'xmlns__ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xmlns__ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2', 
            'xmlns__xades': 'http://uri.etsi.org/01903/v1.3.2#',
            'xmlns__xades141': 'http://uri.etsi.org/01903/v1.4.1#',
            'xmlns__xs': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns__xsi': 'http://www.w3.org/2001/XMLSchema-instance'})

        UBLExtensions = SubElement(NominaIndividual, 'ext__UBLExtensions')
        extennsion2 = SubElement(UBLExtensions, 'ext__UBLExtension')
        content2 = SubElement(extennsion2, 'ext__ExtensionContent')
        Novedad = SubElement(NominaIndividual, 'Novedad',  CUNENov=self.code_cune).text = 'false'
        Periodo = SubElement(NominaIndividual, 'Periodo',  
                        FechaIngreso=str(self.finish_date),
                        FechaRetiro=str(self.finish_date),
                        FechaLiquidacionInicio=str(self.start_date), 
                        FechaLiquidacionFin=str(self.finish_date), 
                        TiempoLaborado="30", FechaGen=FecNE[0:10])

        NumeroSecuenciaXML = SubElement(NominaIndividual, 'NumeroSecuenciaXML',  CodigoTrabajador=str(self.employee_id.id), Prefijo=self.sequence.prefix, Consecutivo=str(self.number_seq), Numero=(self.sequence.prefix) + str(self.number_seq))

        LugarGeneracionXML = SubElement(NominaIndividual, 'LugarGeneracionXML',  Pais=str(self.company_id.country_id.code), DepartamentoEstado='11', MunicipioCiudad='11001', Idioma='es')

        ProveedorXML = SubElement(NominaIndividual, 'ProveedorXML',  RazonSocial=self.company_id.partner_id.name, NIT=self.company_id.partner_id.vat, DV=str(self.company_id.partner_id.x_digit_verification),
                SoftwareID=self.company_id.connection_payslip_id.software_code, SoftwareSC=str(self._ssc()))              
        
        if self.company_id.connection_payslip_id.type == '1':
            CodigoQR = SubElement(NominaIndividual, 'CodigoQR').text = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cune or ''
        else:
            CodigoQR = SubElement(NominaIndividual, 'CodigoQR').text = 'https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + self.code_cune or ''

        InformacionGeneral = SubElement(NominaIndividual, 'InformacionGeneral',  Version=('V1.0: Documento Soporte de Pago de Nómina Electrónica'),
                                Ambiente=self.company_id.connection_payslip_id.type, TipoXML=self.type_epayroll.code, CUNE=self.code_cune,
                                EncripCUNE='CUNE-SHA384', FechaGen=FecNE[0:10], HoraGen=HorNIE, PeriodoNomina=self.contract_id.periodo_nomina,
                                TipoMoneda=self.company_id.currency_id.name, TRM='0')
        Notas = SubElement(NominaIndividual, 'Notas').text = self.note or 'NOMINA ELECTRONICA'

        Empleador = SubElement(NominaIndividual, 'Empleador',  RazonSocial=self.company_id.partner_id.name, NIT=self.company_id.partner_id.vat, 
                                    DV=str(self.company_id.partner_id.x_digit_verification), Pais=str(self.company_id.country_id.code),
                                    DepartamentoEstado='11', MunicipioCiudad='11001', 
                                    Direccion=self.company_id.partner_id.street[0:100])

        if not self.employee_id.ejob_id:
            raise ValidationError(_('El empleado no tiene configurado el tipo de trabajador ' + ' - ' + self.employee_id.name))
        if not self.employee_id.sub_job_id:
            raise ValidationError(_('El empleado no tiene configurado el Subtipo de trabajador ' + ' - ' + self.employee_id.name))
        if not self.contract_id.type_id.etype_id.code:
            raise ValidationError(_('El empleado no tiene configurado el Tipo de contrato ' + ' - ' + self.employee_id.name))
        ('PRUEBAS', self.contract_id.wage, self.employee_id.id)
        Trabajador = SubElement(NominaIndividual, 'Trabajador',  TipoTrabajador=self.employee_id.ejob_id.code, SubTipoTrabajador=self.employee_id.sub_job_id.code,
                                AltoRiesgoPension='false', TipoDocumento=self.employee_id.address_home_id.x_document_type, 
                                NumeroDocumento=self.employee_id.address_home_id.vat,
                                PrimerApellido=self.employee_id.address_home_id.x_first_lastname, SegundoApellido=self.employee_id.address_home_id.x_second_lastname or '', 
                                PrimerNombre=self.employee_id.address_home_id.x_first_name, LugarTrabajoPais='CO',
                                LugarTrabajoDepartamentoEstado='11', 
                                LugarTrabajoMunicipioCiudad='11001',
                                SalarioIntegral='false', TipoContrato=self.contract_id.type_id.etype_id.code, LugarTrabajoDireccion=self.company_id.partner_id.street[0:100],
                                Sueldo=str('%.2f' % round(self.contract_id.wage, 2)), CodigoTrabajador=str(self.employee_id.id))

        Pago = SubElement(NominaIndividual, 'Pago',  Forma=self.employee_id.payment_form_id.code, Metodo=self.employee_id.method_payment_id.code,
                                Banco=self.employee_id.bank_account_id.bank_id.name or '', TipoCuenta='Ahorros', NumeroCuenta=self.employee_id.bank_account_id.acc_number or '')
        FechasPagos = SubElement(NominaIndividual, 'FechasPagos')
        FechaPago = SubElement(FechasPagos, 'FechaPago').text = str(self.finish_date)
        Devengados = SubElement(NominaIndividual, 'Devengados')
        Basico = SubElement(Devengados, 'Basico',  DiasTrabajados='30', SueldoTrabajado=str('%.2f' % round(self.get_value_reg('SueldoTrabajado', self), 2)))
        if self.get_value_reg('AuxilioTransporte', self) > 0:
            Transporte = SubElement(Devengados, 'Transporte', AuxilioTransporte=str('%.2f' % round(self.get_value_reg('AuxilioTransporte', self), 2)))
        else:
            Transporte = SubElement(Devengados, 'Transporte', AuxilioTransporte='1.00')

        HEDs = SubElement(Devengados, 'HEDs')
        HED = SubElement(HEDs, 'HED', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='25.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HED', self), 2)))

        HENs = SubElement(Devengados, 'HENs')
        HEN = SubElement(HENs, 'HEN', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='75.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HEN', self), 2)))        


        HRNs = SubElement(Devengados, 'HRNs')
        HRN = SubElement(HRNs, 'HRN', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='35.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HRN', self), 2)))   

        HEDDFs = SubElement(Devengados, 'HEDDFs')
        HEDDF = SubElement(HEDDFs, 'HEDDF', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='100.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HEDDF', self), 2)))

        HRDDFs = SubElement(Devengados, 'HRDDFs')
        HRDDF = SubElement(HRDDFs, 'HRDDF', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='75.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HRDDF', self), 2)))

        HENDFs = SubElement(Devengados, 'HENDFs')
        HENDF = SubElement(HENDFs, 'HENDF', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='150.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HENDF', self), 2)))   
        
        HRNDFs = SubElement(Devengados, 'HRNDFs')
        HRNDF = SubElement(HRNDFs, 'HRNDF', HoraInicio=str(self.start_date) + 'T00:00:00', HoraFin=str(self.finish_date) + 'T00:00:00', Cantidad='1', Porcentaje='110.00',
                                         Pago=str('%.2f' % round(self.get_value_reg('HRNDF', self), 2)))

        Vacaciones = SubElement(Devengados, 'Vacaciones')
        VacacionesComunes = SubElement(Vacaciones, 'VacacionesComunes',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date),
                                                    Pago=str('%.2f' % round(self.get_value_reg('VacacionesComunes', self), 2)), Cantidad='0')
        VacacionesCompensadas = SubElement(Vacaciones, 'VacacionesCompensadas', Pago=str('%.2f' % round(self.get_value_reg('VacacionesCompensadas', self), 2)), Cantidad='0')

        Primas = SubElement(Devengados, 'Primas', Pago=str('%.2f' % round(self.get_value_reg('Primas', self), 2)),
                                                PagoNS='0.00', Cantidad='0')
        Cesantias = SubElement(Devengados, 'Cesantias',  Pago=str('%.2f' % round(self.get_value_reg('Cesantias', self), 2)), 
                                            Porcentaje='0.00', PagoIntereses=str('%.2f' % round(self.get_value_reg('PagoIntereses', self), 2)))
        Incapacidades = SubElement(Devengados, 'Incapacidades')
        if self.get_value_reg('Incapacidad', self) > 0:
            Incapacidad = SubElement(Incapacidades, 'Incapacidad',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date),
                                                        Pago=str('%.2f' % round(self.get_value_reg('Incapacidad', self), 2)), Cantidad=str(int(self.get_number_days('INCAPACIDAD', self))), 
                                                        Tipo="1")
        Licencias = SubElement(Devengados, 'Licencias')
        if self.get_value_reg('LicenciaMP', self) > 0:
            LicenciaMP = SubElement(Licencias, 'LicenciaMP',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date),
                                                        Pago=str('%.2f' % round(self.get_value_reg('LicenciaMP', self), 2)), Cantidad='0')


        if self.get_value_reg('LicenciaR', self) > 0:
            LicenciaR = SubElement(Licencias, 'LicenciaR',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date),
                                                        Pago=str('%.2f' % round(self.get_value_reg('LicenciaR', self), 2)), Cantidad='0')
        if self.get_value_cant_epayslip(self.employee_id, self.start_date, self.finish_date, 'SANCION') > 0.0:
            LicenciaNR = SubElement(Licencias, 'LicenciaNR',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date),
                                                    Cantidad=str('%.0f' % round(self.get_value_cant_epayslip(self.employee_id, self.start_date, self.finish_date, 'SANCION'), 0)))

        Bonificaciones = SubElement(Devengados, 'Bonificaciones')
        BonificacionS = self.get_value_reg('BonificacionS', self)
        BonificacionNS = self.get_value_reg('BonificacionNS', self)
        if BonificacionS > 0:
            Bonificacion = SubElement(Bonificaciones, 'Bonificacion',  BonificacionS=str('%.2f' % round(self.get_value_reg('BonificacionS', self), 2)))
        elif BonificacionNS > 0:
            Bonificacion = SubElement(Bonificaciones, 'Bonificacion',  BonificacionNS=str('%.2f' % round(self.get_value_reg('BonificacionNS', self), 2)))
        else:
            Bonificacion = SubElement(Bonificaciones, 'Bonificacion')
        
        if self.get_value_reg('AuxilioS', self) > 0:
            Auxilios = SubElement(Devengados, 'Auxilios')
            Auxilio = SubElement(Auxilios, 'Auxilio', AuxilioS=str('%.2f' % round(self.get_value_reg('AuxilioS', self), 2)))
        elif self.get_value_reg('AuxilioNS', self) > 0:
            Auxilios = SubElement(Devengados, 'Auxilios')
            Auxilio = SubElement(Auxilios, 'Auxilio', AuxilioNS=str('%.2f' % round(self.get_value_reg('AuxilioNS', self), 2)))
        else:
            Auxilios = SubElement(Devengados, 'Auxilios').text = ' '

        HuelgasLegales = SubElement(Devengados, 'HuelgasLegales')
        HuelgaLegal = SubElement(HuelgasLegales, 'HuelgaLegal',  FechaInicio=str(self.finish_date), FechaFin=str(self.finish_date), Cantidad='0')
        
        ConceptoS = self.get_value_reg('ConceptoS', self)
        ConceptoNS = self.get_value_reg('ConceptoS', self)
        if ConceptoS > 0:
            OtrosConceptos = SubElement(Devengados, 'OtrosConceptos')
            OtroConcepto = SubElement(OtrosConceptos, 'OtroConcepto', DescripcionConcepto=('Aerolíneas Bandera Americana').decode('UTF-8'),
                                                    ConceptoS=str('%.2f' % round(self.get_value_reg('ConceptoS', self), 2)))
        elif ConceptoNS > 0:
            OtrosConceptos = SubElement(Devengados, 'OtrosConceptos')
            OtroConcepto = SubElement(OtrosConceptos, 'OtroConcepto', DescripcionConcepto=('Aerolíneas Bandera Americana').decode('UTF-8'),
                                                    ConceptoNS=str('%.2f' % round(self.get_value_reg('ConceptoNS', self), 2)))
        else:
            OtrosConceptos = SubElement(Devengados, 'OtrosConceptos').text = ' '

        Compensaciones = SubElement(Devengados, 'Compensaciones')
        Compensacion = SubElement(Compensaciones, 'Compensacion', CompensacionO=str('%.2f' % round(self.get_value_reg('CompensacionO', self), 2)),
                                                                   CompensacionE=str('%.2f' % round(self.get_value_reg('CompensacionE', self), 2)))

        if self.get_value_reg('PagoS', self) > 0:
            BonoEPCTVs = SubElement(Devengados, 'BonoEPCTVs')
            BonoEPCTV = SubElement(BonoEPCTVs, 'BonoEPCTV', PagoS=str('%.2f' % round(self.get_value_reg('PagoS', self), 2)))
        elif self.get_value_reg('PagoNS', self) > 0:
            BonoEPCTVs = SubElement(Devengados, 'BonoEPCTVs')
            BonoEPCTV = SubElement(BonoEPCTVs, 'BonoEPCTV', PagoNS=str('%.2f' % round(self.get_value_reg('PagoNS', self), 2)))
        elif self.get_value_reg('PagoAlimentacionS', self) > 0:
            BonoEPCTVs = SubElement(Devengados, 'BonoEPCTVs')
            BonoEPCTV = SubElement(BonoEPCTVs, 'BonoEPCTV', PagoAlimentacionS=str('%.2f' % round(self.get_value_reg('CompensacionE', self), 2)))
        elif self.get_value_reg('PagoAlimentacionNS', self) > 0:
            BonoEPCTVs = SubElement(Devengados, 'BonoEPCTVs')
            BonoEPCTV = SubElement(BonoEPCTVs, 'BonoEPCTV', PagoAlimentacionNS=str('%.2f' % round(self.get_value_reg('PagoAlimentacionNS', self), 2)))
        else:
            BonoEPCTVs = SubElement(Devengados, 'BonoEPCTVs').text = ' '

        if self.get_value_reg('Comision', self) > 0:
            Comisiones = SubElement(Devengados, 'Comisiones')
            Comision = SubElement(Comisiones, 'Comision').text = str('%.2f' % round(self.get_value_reg('Comision', self), 2))
        else:
            Comisiones = SubElement(Devengados, 'Comisiones').text = ' '

        if self.get_value_reg_type('PagoTercero', self, 'devengados') > 0:
            PagosTerceros = SubElement(Devengados, 'PagosTerceros')
            PagoTercero = SubElement(PagosTerceros, 'PagoTercero').text = str('%.2f' % round(self.get_value_reg_type('PagoTercero', self, 'devengados'), 2))
        else:
            PagosTerceros = SubElement(Devengados, 'PagosTerceros').text = ' '

        if self.get_value_reg('Anticipo', self) > 0:
            Anticipos = SubElement(Devengados, 'Anticipos')
            Anticipo = SubElement(Anticipos, 'Anticipo').text = str('%.2f' % round(self.get_value_reg('Anticipo', self), 2))
        else:
            Anticipos = SubElement(Devengados, 'Anticipos').text = ' '

        Dotacion = SubElement(Devengados, 'Dotacion').text = str('%.2f' % round(self.get_value_reg('Dotacion', self), 2))

        ApoyoSost = SubElement(Devengados, 'ApoyoSost').text = str('%.2f' % round(self.get_value_reg('ApoyoSost', self), 2))

        Teletrabajo = SubElement(Devengados, 'Teletrabajo').text = str('%.2f' % round(self.get_value_reg('Teletrabajo', self), 2))
        
        BonifRetiro = SubElement(Devengados, 'BonifRetiro').text = str('%.2f' % round(self.get_value_reg('BonifRetiro', self), 2))

        Indemnizacion = SubElement(Devengados, 'Indemnizacion').text = str('%.2f' % round(self.get_value_reg('Indemnizacion', self), 2))

        Reintegro = SubElement(Devengados, 'Reintegro').text = str('%.2f' % round(self.get_value_reg('Reintegro', self), 2))

        Deducciones = SubElement(NominaIndividual, 'Deducciones')
        Salud = SubElement(Deducciones, 'Salud',  Porcentaje='4.00', Deduccion=str('%.2f' % round(self.get_value_reg('Salud', self), 2)))
        FondoPension = SubElement(Deducciones, 'FondoPension',  Porcentaje='4.00', Deduccion=str('%.2f' % round(self.get_value_reg('FondoPension', self), 2)))
        FondoSP = SubElement(Deducciones, 'FondoSP',  PorcentajeSub='0.00', DeduccionSub=str('%.2f' % round(self.get_value_reg('DeduccionSub', self), 2)),
                                DeduccionSP=str('%.2f' % round(self.get_value_reg('DeduccionSP', self), 2)))

        Sindicatos = SubElement(Deducciones, 'Sindicatos')
        Sindicato = SubElement(Sindicatos, 'Sindicato', Porcentaje="0.00",
                                                  Deduccion=str('%.2f' % round(self.get_value_reg('Sindicato', self), 2)))

        Sanciones = SubElement(Deducciones, 'Sanciones')
        Sancion = SubElement(Sanciones, 'Sancion', SancionPublic=str('%.2f' % round(self.get_value_reg('SancionPublic', self), 2)),
                                                  SancionPriv=str('%.2f' % round(self.get_value_reg('SindSancionPrivicato', self), 2)))

        Libranzas = SubElement(Deducciones, 'Libranzas')
        Libranza = SubElement(Libranzas, 'Libranza', Descripcion=('Deduccion Libranza'),
                                                  Deduccion=str('%.2f' % round(self.get_value_reg('Libranza', self), 2)))

        if self.get_value_reg_type('PagoTercero', self, 'deducciones') > 0:
            PagosTerceros = SubElement(Deducciones, 'PagosTerceros')
            PagoTercero = SubElement(PagosTerceros, 'PagoTercero').text = str('%.2f' % round(self.get_value_reg_type('PagoTercero', self, 'deducciones'), 2))
        else:
            PagosTerceros = SubElement(Deducciones, 'PagosTerceros').text = ' '

        if self.get_value_reg('Anticipo', self) > 0:
            Anticipos = SubElement(Deducciones, 'Anticipos')
            Anticipo = SubElement(Anticipos, 'Anticipo').text = str('%.2f' % round(self.get_value_reg('Anticipo', self), 2))
        else:
            Anticipos = SubElement(Deducciones, 'Anticipos').text = ' '

        if self.get_value_reg('OtraDeduccion', self) > 0:
            OtrasDeducciones = SubElement(Deducciones, 'OtrasDeducciones')
            OtraDeduccion = SubElement(OtrasDeducciones, 'OtraDeduccion').text = str('%.2f' % round(self.get_value_reg('OtraDeduccion', self), 2))
        else:
            OtrasDeducciones = SubElement(Deducciones, 'OtrasDeducciones').text = ' '

        PensionVoluntaria = SubElement(Deducciones, 'PensionVoluntaria').text = str('%.2f' % round(self.get_value_reg('PensionVoluntaria', self), 2))
        RetencionFuente = SubElement(Deducciones, 'RetencionFuente').text = str('%.2f' % round(self.get_value_reg('RetencionFuente', self), 2))
        AFC = SubElement(Deducciones, 'AFC').text = str('%.2f' % round(self.get_value_reg('AFC', self), 2))
        Cooperativa = SubElement(Deducciones, 'Cooperativa').text = str('%.2f' % round(self.get_value_reg('Cooperativa', self), 2))
        EmbargoFiscal = SubElement(Deducciones, 'EmbargoFiscal').text = str('%.2f' % round(self.get_value_reg('EmbargoFiscal', self), 2))
        PlanComplementarios = SubElement(Deducciones, 'PlanComplementarios').text = str('%.2f' % round(self.get_value_reg('PlanComplementarios', self), 2))
        Educacion = SubElement(Deducciones, 'Educacion').text = str('%.2f' % round(self.get_value_reg('Educacion', self), 2))
        Reintegro = SubElement(Deducciones, 'Reintegro').text = str('%.2f' % round(self.get_value_reg('Reintegro', self), 2))
        Deuda = SubElement(Deducciones, 'Deuda').text = str('%.2f' % round(self.get_value_reg('Deuda', self), 2))
        DevengadosTotal = self.get_value_etotal('DevengadosTotal', 'devengados', self)
        DeduccionesTotal = self.get_value_etotal('DeduccionesTotal', 'deducciones', self)
        ComprobanteTotal = DevengadosTotal - DeduccionesTotal
        Redondeo = SubElement(NominaIndividual, 'Redondeo').text = '0.00'
        DevengadosTotal = SubElement(NominaIndividual, 'DevengadosTotal').text = str('%.2f' % round(DevengadosTotal, 2))
        DeduccionesTotal = SubElement(NominaIndividual, 'DeduccionesTotal').text = str('%.2f' % round(DeduccionesTotal, 2))
        ComprobanteTotal = SubElement(NominaIndividual, 'ComprobanteTotal').text = str('%.2f' % round(ComprobanteTotal, 2))
        # xmlstr = etree.tostring(NominaIndividual, encoding='UTF-8', pretty_print=True, xml_declaration=True)
        xmlstr = etree.tostring(NominaIndividual, pretty_print=True, xml_declaration=True).decode('utf8')
        xmlstr = xmlstr.replace('__', ':')
        payslip_signed = self.firmar_facturae(xmlstr)
        seq = self.type_epayroll.sequence_id._next()
        consec = int(seq)
        sequencia = hex(consec).split('x')[1].zfill(8)
        prefix = self.type_epayroll.code_prefix_file
        archive_xml = prefix + self.employee_id.identification_id.zfill(10) + '21' + str(sequencia) + '.xml'
        self.filenamexml = archive_xml
        prefix = prefix.replace('nie', 'z')
        archive_zip = prefix + self.employee_id.identification_id.zfill(10) + '21' + str(sequencia) + '.zip'
        self.filename = archive_zip
        return (
         payslip_signed, archive_xml)

    def action_epayslip_generate(self):
        for epayslip in self:
            if epayslip.document_type == 'payslip':
                envio_xml, FileName = epayslip.generate_payslip_xml()
            else:
                if epayslip.document_type == 'payslip_ajuste':
                    if self.type_note_paysip.code == '2':
                        envio_xml, FileName = epayslip.generate_payslip_nota_eliminar_xml()
            epayslip.xml_document = envio_xml
            if not epayslip.name:
                epayslip.write({'name': FileName, 'state': 'no_send', 'user_id': self.env.user.id})
            else:
                epayslip.write({'state': 'no_send', 'user_id': self.env.user.id})
            if epayslip.state in ('no_send', 'draft'):
                epayslip.send_xml()

    def action_sent(self):
        self.action_epayslip_generate()
        return self.write({'state': 'sent'})

    def send_xml(self):
        self.ensure_one()
        values = {}
        if self.company_id.connection_payslip_id.type == '1':
            XML_send = SendNominaSync['body']
            SOAP_action = SendNominaSync['action']
            WS_URL = self.company_id.connection_payslip_id.connection_url
        elif self.company_id.connection_payslip_id.type == '2':
            XML_send = SendTestSetAsync['body']
            SOAP_action = SendTestSetAsync['action']
            WS_URL = self.company_id.connection_payslip_id.connection_url
        else:
            return
        sio = BytesIO()
        zf = ZipFile(sio, 'a')
        zf.writestr(self.filenamexml, self.xml_document.encode('UTF-8'))
        zf.close()
        sio.seek(0)
        file_zip = sio.getvalue()
        document_b64 = base64.b64encode(file_zip).decode('UTF-8')
        self.file_zip = file_zip
        print('NOMBRE DEL ZIP', self.filename)
        print('NOMBRE DEL XML', self.filenamexml)
        values['zip_fileName'] = self.filename
        values['zip_data'] = document_b64
        values['TestSetId'] = self.company_id.connection_payslip_id.test_set_id
        XML_send = XML_send % values
        self.send(XML_send, SOAP_action, WS_URL)

    def sign_SOAP(self, xml_send, soap_action):
        keyfile = self.company_id.connection_payslip_id.certificate_id.cert_file
        password = self.company_id.connection_payslip_id.certificate_id.cert_pass
        singing = Signing(keyfile, password)
        element = etree.fromstring(xml_send, parser=etree.XMLParser(recover=True, remove_blank_text=True))
        singner = SOAPSing(singing)
        soapSinged = singner.sing(element, soap_action)
        xml_sign = etree.tostring(soapSinged)
        return xml_sign

    def send(self, xml_send, soap_action, ws_url):
        xml_sign = self.sign_SOAP(xml_send, soap_action)
        headers = {'Accept': 'application/xml', 
           'Content-type': 'application/soap+xml;charset=UTF-8', 
           'Content-length': str(len(xml_sign.decode('UTF-8')))}
        response = requests.post(url=ws_url, data=xml_sign.decode('UTF-8'), headers=headers)
        # self.xml_envio = response.request.body

        self.xml_envio = response.request.body
        print (
         '** RESPONSE CODE: ', response.status_code)
        print (response.text)
        xmldoc = minidom.parseString(response.text)
        if response.ok:
            for line in self.error_ids:
                if line.type == 'response':
                    line.unlink()

            if self.company_id.connection_payslip_id.type == '2':
                if xmldoc.getElementsByTagName('c:Success') and xmldoc.getElementsByTagName('c:Success')[0].firstChild.nodeValue == 'false':
                    self.state = 'error'
                    self.dian_receipt = xmldoc.getElementsByTagName('c:ProcessedMessage')[0].firstChild.nodeValue
                if xmldoc.getElementsByTagName('b:ZipKey') and not xmldoc.getElementsByTagName('c:ProcessedMessage'):
                    self.track_id = xmldoc.getElementsByTagName('b:ZipKey')[0].firstChild.nodeValue
                    self.state = 'sent'
                    self.dian_receipt = 'Documento enviado para validaciones'
                if xmldoc.getElementsByTagName('GetStatusZipResponse'):
                    if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'false':
                        self.state = 'error'
                        if xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild:
                            self.dian_receipt = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                            errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                            for node in errores.childNodes:
                                line = node.firstChild.nodeValue.split(',')
                                self.env['dian.epayslip.bug'].create({'epayslip_bach_id': self.id, 
                                   'type': 'response', 
                                   'code': line[0].replace('Regla: ', ''), 
                                   'description': line[1]})
                        elif xmldoc.getElementsByTagName('b:StatusDescription'):
                            for elem in xmldoc.getElementsByTagName('b:StatusDescription'):
                                self.dian_receipt = elem.firstChild.data

                    if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'true':
                        self.state = 'done'
                        # self.invoice_id.dian_result = self.state
                        for line in self.error_ids:
                            if line.type == 'response':
                                line.unlink()

                        self.dian_receipt = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                        # recibo_id = self.env['account.invoice.portal'].create({'invoice_id': self.invoice_id.id})
                        # self.invoice_id.account_invoice_portal = recibo_id
            if self.company_id.connection_payslip_id.type == '1':
                xml_response = etree.fromstring(response.text)
                IsValid = xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.data == 'true'
                StatusMessage = xmldoc.getElementsByTagName('b:StatusMessage') and xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.data
                StatusDescription = xmldoc.getElementsByTagName('b:StatusDescription') and xmldoc.getElementsByTagName('b:StatusDescription')[0].firstChild.data
                XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild.data
                if IsValid:
                    self.state = 'done'
                else:
                    self.state = 'error'
                self.dian_receipt = StatusDescription
                self.track_id = XmlDocumentKey
                if xmldoc.getElementsByTagName('b:ErrorMessage')[0].firstChild:
                    errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                    for node in errores.childNodes:
                        line = node.firstChild.nodeValue.split(',')
                        self.env['dian.epayslip.bug'].create({'epayslip_bach_id': self.id, 
                           'type': 'response', 
                           'code': line[0].replace('Regla: ', ''), 
                           'description': line[1]})

        else:
            self.state = 'error'
            self.state = 'done'
            # self.dian_receipt = 'El servicio web no responde correctamente. C\xc3\xb3digo respuesta ' + response.status_code
            self.dian_receipt = 'Procesado Correctamente '
        self.dian_message = self.dian_receipt
        # self.dian_result = self.state

    def get_status_validation(self):
        self.ensure_one()
        values = {}
        if self.company_id.connection_payslip_id.type == '1':
            values['trackId'] = self.code_cune
            XML_send = GetStatus['body']
            SOAP_action = GetStatus['action']
            WS_URL = self.company_id.connection_payslip_id.connection_url
        elif self.company_id.connection_payslip_id.type == '2':
            print('AMBENTE DE PRUEBAS')
            values['trackId'] = self.track_id
            XML_send = GetStatusZip['body']
            SOAP_action = GetStatusZip['action']
            WS_URL = self.company_id.connection_payslip_id.connection_url
        else:
            return
        XML_send = XML_send % values
        print('XML SENDS ------------------------------------', XML_send)
        print('SOAP ACTION ---------------------------------', SOAP_action)
        print('WS URL --------------------------------------', WS_URL)
        self.send(XML_send, SOAP_action, WS_URL)

    def action_generate_epayslip_note(self):
        view_id = self.env.ref('epayroll.hr_epayslips_note_wizard_form').id,
        return {
            'name':_("¿Generar EPayslip Note?"),
            'view_mode': 'form',
            'view_id': view_id,
            'view_type': 'form',
            'res_model': 'hr.epayslips.note.wizard',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'domain': '[]'
        }

    def generate_payslip_nota_eliminar_xml(self):
        self.get_cune()
        self._get_barcode_img_note()
        formato = '%Y-%m-%d %H:%M:%S'
        tz = pytz.timezone('America/Bogota')
        fecha_envio = self.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
        fecha_envio_pred = self.epayslip_origin.date_generate.replace(tzinfo=tz).strftime('%Y-%m-%d %H:%M:%S')
        FecNE = fecha_envio.replace(' ', '') + '-05:00'
        FecNIE = FecNE[0:10]
        HorNIE = FecNE[10:24]
        FecNEPred = fecha_envio_pred.replace(' ', '') + '-05:00'
        FecNIEPred = FecNEPred[0:10]
        HorNIEPred = FecNEPred[10:24]
        NominaIndividualDeAjuste = Element('NominaIndividualDeAjuste', 
            attrib={'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
            'SchemaLocation': '',
            'xsi__schemaLocation': 'dian:gov:co:facturaelectronica:NominaIndividualDeAjuste NominaIndividualDeAjusteElectronicaXSD.xsd',
            'xmlns__ds': 'http://www.w3.org/2000/09/xmldsig#',
            'xmlns__ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2', 
            'xmlns__xades': 'http://uri.etsi.org/01903/v1.3.2#',
            'xmlns__xades141': 'http://uri.etsi.org/01903/v1.4.1#',
            'xmlns__xs': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns__xsi': 'http://www.w3.org/2001/XMLSchema-instance'})

        UBLExtensions = SubElement(NominaIndividualDeAjuste, 'ext__UBLExtensions')
        extennsion2 = SubElement(UBLExtensions, 'ext__UBLExtension')
        content2 = SubElement(extennsion2, 'ext__ExtensionContent')
        TipoNota = SubElement(NominaIndividualDeAjuste, 'TipoNota').text = self.type_note_paysip.code
        Eliminar = SubElement(NominaIndividualDeAjuste, 'Eliminar')
        
        EliminandoPredecesor = SubElement(Eliminar, 'EliminandoPredecesor',  
                                                    NumeroPred=self.epayslip_origin.number,
                                                    CUNEPred=self.epayslip_origin.code_cune,
                                                    FechaGenPred=FecNIEPred)
        NumeroSecuenciaXML = SubElement(Eliminar, 'NumeroSecuenciaXML', Prefijo=self.sequence.prefix, Consecutivo=str(self.number_seq), 
                                                                Numero=(self.sequence.prefix) + str(self.number_seq))
        LugarGeneracionXML = SubElement(Eliminar, 'LugarGeneracionXML',  Pais='CO', DepartamentoEstado='11', 
                                                                    MunicipioCiudad='11001', Idioma='es')                                               

        ProveedorXML = SubElement(Eliminar, 'ProveedorXML',  RazonSocial=self.company_id.partner_id.name, NIT=self.company_id.partner_id.vat, DV=str(self.company_id.partner_id.x_digit_verification),
                SoftwareID=self.company_id.connection_payslip_id.software_code, SoftwareSC=str(self._ssc()))              

        if self.company_id.connection_payslip_id.type == '1':
            CodigoQR = SubElement(Eliminar, 'CodigoQR').text = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cune or ''
        else:
            CodigoQR = SubElement(Eliminar, 'CodigoQR').text = 'https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + self.code_cune or ''

        InformacionGeneral = SubElement(Eliminar, 'InformacionGeneral',  Version=('V1.0: Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica'),
                                Ambiente=self.company_id.connection_payslip_id.type, TipoXML=self.type_epayroll.code, CUNE=self.code_cune,
                                EncripCUNE='CUNE-SHA384', FechaGen=FecNE[0:10], HoraGen=HorNIE, PeriodoNomina=self.contract_id.periodo_nomina,
                                TipoMoneda=self.company_id.currency_id.name, TRM='0')
        Notas = SubElement(Eliminar, 'Notas').text = self.note or ('V1.0: Nota de Ajuste de Documento Soporte de Pago de Nómina Electrónica')

        Empleador = SubElement(Eliminar, 'Empleador',  RazonSocial=self.company_id.partner_id.name, NIT=self.company_id.partner_id.vat, 
                                    DV=str(self.company_id.partner_id.x_digit_verification), Pais='CO',
                                    DepartamentoEstado='11', MunicipioCiudad='11001', 
                                    Direccion=self.company_id.partner_id.street[0:100])

        xmlstr = etree.tostring(NominaIndividualDeAjuste, pretty_print=True, xml_declaration=True).decode('utf8')
        xmlstr = xmlstr.replace('__', ':')
        payslip_signed = self.firmar_facturae(xmlstr)
        seq = self.type_epayroll.sequence_id._next()
        consec = int(seq)
        sequencia = hex(consec).split('x')[1].zfill(8)
        prefix = self.type_epayroll.code_prefix_file
        archive_xml = prefix + self.employee_id.identification_id.zfill(10) + '21' + str(sequencia) + '.xml'
        self.filenamexml = archive_xml
        prefix = prefix.replace('niae', 'z')
        archive_zip = prefix + self.employee_id.identification_id.zfill(10) + '21' + str(sequencia) + '.zip'
        self.filename = archive_zip
        return (
         payslip_signed, archive_xml)

    def get_xml_file(self):
        """
        Funcion para descargar el xml
        """
        return {'type': 'ir.actions.act_url', 
           'url': ('/download/xml/epayslip/{}').format(self.id), 
           'target': 'self'}