# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from os import write
from dateutil.relativedelta import relativedelta
import pytz

import random
import io
from io import BytesIO
from zipfile import ZipFile
from xml.dom import minidom

import pem, xmlsig, logging
from lxml import etree
from lxml.etree import Element, SubElement
import xml.etree.ElementTree as ET

from pytz import timezone
from six import string_types
from random import randint
import zipfile

from odoo import models, fields, api, _
from odoo.addons.edoc_sop_logyca.models.template_xml import *
from odoo.addons.edoc_sop_logyca.REQUESTDian.Signing import Signing
from odoo.addons.edoc_sop_logyca.REQUESTDian.SOAPSing import SOAPSing
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tools.misc import formatLang, format_date, get_lang


_logger = logging.getLogger(__name__)

try:
    import pyqrcode
except ImportError:
    _logger.warning('Cannot import pyqrcode library ***********************')

try:
    import requests 
except ImportError:
    _logger.warning("no se ha cargado requests")

try:
    import hashlib
except ImportError:
    _logger.warning('Cannot import hashlib library')

try:
    from lxml import etree
except ImportError:
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
except ImportError:
    _logger.warning('Cannot import OpenSSL library')

try:
    import base64
except ImportError:
    _logger.warning('Cannot import base64 library ***********************')

try:
    import uuid
except ImportError:
    _logger.warning('Cannot import uuid library')
    
try:
    import gzip
except ImportError:
    _logger.warning("no se ha cargado gzip ***********************")

try:
    import zlib
    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED


class AccountMove(models.Model):
    _inherit = "account.move"

    ds_date = fields.Datetime('Fecha y hora', readonly=True, help='Date of Invoice with Time Zone', copy=False)
    xml_ds_document = fields.Text(string='Contenido XML DS', copy=False, readonly=True,
                                        state_doc_sop={'draft': [('readonly', False)]})
    ds_name = fields.Char('File DS Name')
    filename_ds = fields.Char(string='Nombre del archivo', required=False, readonly=True, states={'draft': [('readonly', False)]})
    state_doc_sop = fields.Selection([
                        ('draft', 'Draft'),
                        ('no_send', 'Not Send'),
                        ('error', 'With Error'),
                        ('send', 'Send'),
                        ('done', 'Done'),
                        ('rejected', 'Rejected')], default='draft')
    user_ds_id = fields.Many2one('res.users', string='User DS')
    code_qr_ds = fields.Text(copy=False, string='Codigo QR DS', help='Code QR DS')
    QR_code_ds = fields.Binary(string=_('Code QR DS'), help='Code QR DS')
    code_cuds = fields.Char('CUDS', readonly=True, copy=False)
    form_send_ds_id = fields.Many2one('form.send.ds', string='Forma de generación y transmisión')
    url_dian_ds = fields.Char('URL DIAN DS')
    type_operation_ds = fields.Many2one('type.operation.ds', string='Operation Type DS')
    type_document_id = fields.Many2one('type.edocument', related='journal_id.type_document_id')
    einvice_payment_id = fields.Many2one('mode.payment.einvoice',
                                         string='mode payment einvoice',
                                         readonly=True,
                                         states={'draft': [
                                             ('readonly', False)
                                         ]})
    einvice_form_type_id = fields.Selection(
        related='invoice_payment_term_id.einvice_form_payment_id.type', string='Formas de Pago')
    bug_ds_ids = fields.One2many(
        'eresponse.bugs', 'send_ds_id', string='Errores DS')
    track_ds_id = fields.Char(string='Track DS ID', required=False, readonly=True, states={
                              'draft': [('readonly', False)]})
    xml_envio_ds = fields.Text(string='XML Eviado', required=False, readonly=True, copy=False, states={
                               'draft': [('readonly', False)]})
    dian_receipt_ds = fields.Text(string='Mensaje recepci', copy=False, readonly=False, states={
                                  'Done': [('readonly', False)], 'Rejected': [('readonly', False)]})

    def _acortar_str(self, texto, size=1):
        c = 0
        cadena = ''
        while c < size and c < len(texto):
            cadena += texto[c]
            c += 1
        return cadena

    def _ssc_ds(self):
        if self.journal_id.type_document_id.ecode == '20':
            return hashlib.new('sha384', (str(self.company_id.connection_pos_id.software_code) + str(self.company_id.connection_pos_id.pin_software) + str(self.name)).encode('utf-8')).hexdigest()
        else:
            return hashlib.new('sha384', (str(self.company_id.connection_doc_sop_id.software_code) + str(self.company_id.connection_doc_sop_id.pin_software) + str(self.name)).encode('utf-8')).hexdigest()

    @api.model
    def _get_date_timezone(self):
        # TODO: remove deprecated variables
        format_str = '%Y-%m-%d %H:%M:%S'
        time_zone = pytz.timezone('America/Bogota')
        einvoice_date = datetime.now(time_zone).strftime(format_str)
        date_invoice = datetime.now()
        return date_invoice

    def action_ds_generate_move(self):
        for emove in self:
            emove.action_ds_generate()

    def action_ds_generate(self):
        self.ds_date = self._get_date_timezone()
        if self.journal_id.type_document_id and self.journal_id.type_document_id.document_type == 'ds':
            envio_xml, FileName = self.generate_ds_xml()
        self.xml_ds_document = envio_xml
        if not self.ds_name:
            self.write({'ds_name': FileName, 'state_doc_sop': 'no_send', 'user_ds_id': self.env.user.id})
        else:
            self.write({'state_doc_sop': 'no_send', 'user_ds_id': self.env.user.id, 'ds_name': FileName,})
        if self.state_doc_sop in ('no_send', 'draft'):
            self.send_xml_ds()

    def cuds(self):
        for inv in self:
            if inv.state in ('draft', 'cancel') or not inv.name:
                return
            if inv.journal_id.type_document_id and inv.journal_id.type_document_id.document_type == 'ds' and not inv.journal_id.einvoice_journal:
                raise ValidationError('El diario %s no tiene asociada una resolucin de facturacin DIAN' % (inv.journal_id.name,))
            NumDS = inv.name
            if inv.ds_date:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                fecha_envio = self.ds_date.replace(tzinfo=tz).strftime(formato)
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                FecDS = FecNE[0:10]
                HorDS = FecNE[10:15] + '-05:00'
                HorDS = FecNE[10:24]
            else:
                FecDS = ''
                HorDS = ''
            ValDS = str('%.2f' % round(inv.amount_untaxed, 2))
            CodImp = '01'
            CodImp2 = '04'
            CodImp3 = '03'
            ValImp = 0.00
            ValImp2 = 0.00
            ValImp2 = str('%.2f' % round((ValImp2), 2))
            ValImp3 = 0.00
            ValImp3 = str('%.2f' % round((ValImp3), 2))
            for tax_line in inv.line_ids:
                if tax_line.tax_line_id and tax_line.tax_group_id:
                    if tax_line.tax_group_id and not tax_line.tax_group_id.tributo_id.code:
                        continue
                        # raise ValidationError(u'El impuesto %s no presenta cdigo de impuesto DIAN' % (
                        #  tax_line.tax_line_id.name,))
                    if tax_line.tax_group_id.tributo_id.code == CodImp:
                        ValImp += round(abs(tax_line.credit), 2)
            ValIVA = ValImp
            ValTot = str('%.2f' % round((inv.amount_untaxed+ValIVA), 2))
            ValIVA = str('%.2f' % round((ValImp), 2))
            NITABS = inv.company_id.partner_id.vat or ''
            NumSNO = inv.partner_id.vat or ''
            Software = inv.company_id.connection_doc_sop_id.pin_software
            TipoAmbiente = inv.company_id.connection_doc_sop_id.type
            print('TIPO', TipoAmbiente)
            if not TipoAmbiente:
                raise ValidationError(u'Debe configurar el ambiente de FE en la company')
            cuds = NumDS + FecDS + HorDS + ValDS + CodImp + ValIVA + ValTot + NumSNO + NITABS + Software + TipoAmbiente
            if self.journal_id.type_document_id.ecode == '20':
                cuds = NumDS + FecDS + HorDS + ValDS + CodImp + ValIVA + CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot + NITABS + NumSNO + Software + TipoAmbiente
            return cuds
        return

    def _cuds(self):
        cuds = self.cuds()
        if cuds == None:
            return
        else:
            sha384 = hashlib.sha384(cuds.encode('utf-8'))
            code_cuds = sha384.hexdigest()
            self.write({'code_cuds': code_cuds})
            if self.journal_id.type_document_id.ecode == '20':
                self.write({'code_cufe': code_cuds})
            return code_cuds

    def _get_barcode_img_docsp(self):
        for inv in self:
            if not inv.invoice_date:
                return
            if not inv.code_cuds:
                cuds = inv._cuds()
            else:
                cuds = inv.code_cuds
            NumFac = inv.name
            if inv.ds_date:
                formato = '%Y-%m-%d %H:%M:%S'
                tz = pytz.timezone('America/Bogota')
                fecha_envio = self.ds_date.replace(tzinfo=tz).strftime(formato)
                FecNE = fecha_envio.replace(' ', '') + '-05:00'
                FecFac = FecNE[0:10]
                Hor_Emi = FecNE[10:24]
            else:
                FecFac = ''
                Hor_Emi = ''
            NitFac = inv.company_id.partner_id.vat or ''
            DocAdq = inv.partner_id.vat or ''
            ValFac = str('%.2f' % round(inv.amount_untaxed, 2))
            ValFacIm = str('%.2f' % round(inv.amount_total, 2))
            ValIva = 0
            ValOtroIm = 0
            for tax_line in inv.line_ids:
                if tax_line.tax_line_id and tax_line.tax_group_id:
                    if tax_line.tax_group_id and not tax_line.tax_group_id.tributo_id.code:
                        continue
                    if tax_line.tax_group_id.tributo_id.code == '01':
                        ValIva += tax_line.credit
                    else:
                        ValOtroIm += tax_line.credit
            if cuds == None:
                cuds = ''
            if not NumFac:
                NumFac = ''
            NITABS = inv.company_id.partner_id.vat or ''
            NumSNO = inv.partner_id.vat or ''
            if self.journal_id.type_document_id.ecode == '20':
                Software = inv.company_id.connection_pos_id.pin_software
                TipoAmbiente = inv.company_id.connection_pos_id.type
            else:
                Software = inv.company_id.connection_doc_sop_id.pin_software
                TipoAmbiente = inv.company_id.connection_doc_sop_id.type

            if TipoAmbiente == 2:
                # texto = 'N°DocSoporte=' + NumFac + '                 Fecha=' + FecFac + '                 Hora=' + Hor_Emi + '                 ValDS=' + ValFac + '                 CodImp=' + '01' + '                 ValImp=' + str(ValIva) + '                 ValTot=' + ValFacIm  + '                 NumSNO=' + NumSNO + '                 NITABS=' + NITABS + '                 PIN=' + Software  + '                 Amb=' + TipoAmbiente + '                 CUDS=' + cuds + '                 URL=https://catalogo-vpfe-hab.dian.gov.co/Document/FindDocument?documentKey=' + cuds
                # texto = 'NumDS=' + NumFac + '                 FecDS=' + FecFac + '                 HorDS=' + Hor_Emi + '                 NumSNO=' + NumSNO + '                 NITABS=' + NITABS + '                 ValDS=' + ValFac +  '                 ValIva=' + str(ValIva) + '                 ValTolDS=' + ValFac  + '                 CUFE=' + cuds + '                 https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + cuds
                texto = 'NroFactura=' + NumFac + '                 NitFacturador=' + NITABS + '        NitAdquiriente=' + NumSNO + '               FechaFactura=' + FecFac +  '                 ValorTotalFactura=' + ValFac + '           CUFE=' + cuds + '                 https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + cuds
            else:
                # texto = 'N°DocSoporte=' + NumFac + '                 Fecha=' + FecFac + '                 Hora=' + Hor_Emi + '                 ValDS=' + ValFac + '                 CodImp=' + '01' + '                 ValImp=' + str(ValIva) + '                 ValTot=' + ValFacIm  + '                 NumSNO=' + NumSNO + '                 NITABS=' + NITABS + '                 PIN=' + Software  + '                 Amb=' + TipoAmbiente + '                 CUDS=' + cuds + '                 URL=https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + cuds
                # texto = 'NumDS=' + NumFac + '                 FecDS=' + FecFac + '                 HorDS=' + Hor_Emi + '                 NumSNO=' + NumSNO + '                 NITABS=' + NITABS + '                 ValDS=' + ValFac +  '                 ValIva=' + str(ValIva) + '                 ValTolDS=' + ValFac  + '                 CUFE=' + cuds + '                 https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + cuds
                texto = 'NroFactura=' + NumFac + '                 NitFacturador=' + NITABS + '        NitAdquiriente=' + NumSNO + '               FechaFactura=' + FecFac +  '                 ValorTotalFactura=' + ValFac + '           CUFE=' + cuds + '                 https://catalogo-vpfe-hab.dian.gov.co/document/searchqr?documentkey=' + cuds

            qr_code = pyqrcode.create(texto)
            inv.write({'code_qr_ds': texto})
            img_as_str = qr_code.png_as_base64_str(scale=5)
            inv.QR_code_ds = img_as_str
        return texto

    def _rangos_ds(self, rangos):
        if self.journal_id.type_document_id.ecode == '20':
            if not self.company_id.connection_pos_id:
                raise ValidationError('Debe configurar en la compañía %s la conexión a la DIAN' % (
                    self.company_id.name,))
        else:
            if not self.company_id.connection_doc_sop_id:
                raise ValidationError('Debe configurar en la compañía %s la conexión a la DIAN' % (
                    self.company_id.name,))
        rango = self.journal_id.sequence_id.dian_resolution_ids
        print('RANGOOO', rango)
        if not rango:
            raise ValidationError('El diario %s no tiene una resolución electrónica para Documento Soporte, por favor agreguela o cambie la configuración diario' % (
                self.journal_id.name,))            
        exten = SubElement(rangos, 'ext__UBLExtension')
        content = SubElement(exten, 'ext__ExtensionContent')
        dianExt = SubElement(content, 'sts__DianExtensions')
        ic = SubElement(dianExt, 'sts__InvoiceControl')
        SubElement(ic, 'sts__InvoiceAuthorization').text = rango.resolution_number
        auth = SubElement(ic, 'sts__AuthorizationPeriod')
        SubElement(auth, 'cbc__StartDate').text = str(rango.date_from)
        SubElement(auth, 'cbc__EndDate').text = str(rango.date_to)
        auth_inv = SubElement(ic, 'sts__AuthorizedInvoices')
        SubElement(auth_inv, 'sts__Prefix').text = rango.resolution_prefix or ''
        SubElement(auth_inv, 'sts__From').text = str(rango.from_range)
        SubElement(auth_inv, 'sts__To').text = str(rango.to_range)
        inv_sec = SubElement(dianExt, 'sts__InvoiceSource')
        SubElement(inv_sec, 'cbc__IdentificationCode', attrib={'listAgencyID': '6', 'listAgencyName': 'United Nations Economic Commission for Europe', 'listSchemeURI': 'urn:oasis:names:specification:ubl:codelist:gc:CountryIdentificationCode-2.1'}).text = 'CO'
        sp = SubElement(dianExt, 'sts__SoftwareProvider')
        if not self.company_id.partner_id.x_document_type:
            raise ValidationError('El tipo de identificación %s no tiene código DIAN en el tercero de la compañía' % (
                self.company_id.partner_id.x_document_type,))
        print('uuuuyuyuyuy',self.company_id.partner_id.x_digit_verification)
        if not self.company_id.partner_id.x_digit_verification and self.company_id.partner_id.x_digit_verification != 0:
            raise ValidationError('El tercero de la compañía no tiene configurado el dígito de verificación %s ' % (
                self.company_id.partner_id.name,))
        if not self.company_id.partner_id.vat:
            raise ValidationError('El tercero de la compañía no tiene configurado el número de identificación %s ' % (
                self.company_id.partner_id.name,))
        SubElement(sp, 'sts__ProviderID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}, schemeID=str(self.company_id.partner_id.x_digit_verification), schemeName=str(self.company_id.partner_id.x_document_type)).text = self.company_id.partner_id.vat
        if self.journal_id.type_document_id.ecode == '20':
            SubElement(sp, 'sts__SoftwareID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}).text = self.company_id.connection_pos_id.software_code
        else:
            SubElement(sp, 'sts__SoftwareID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}).text = self.company_id.connection_doc_sop_id.software_code
        SubElement(dianExt, 'sts__SoftwareSecurityCode', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}).text = str(self._ssc_ds())
        aut_pro = SubElement(dianExt, 'sts__AuthorizationProvider')
        SubElement(aut_pro, 'sts__AuthorizationProviderID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)', 'schemeID': '4', 'schemeName': '31'}).text = '800197268'
        self._get_barcode_img_docsp()
        SubElement(dianExt, 'sts__QRCode').text = self.code_qr_ds or ''

    def generate_ds_xml(self):
        Invoice = Element('Invoice', attrib={'xmlns': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2', 
           'xmlns__cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2', 
           'xmlns__cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2', 
           'xmlns__ds': 'http://www.w3.org/2000/09/xmldsig#', 
           'xmlns__ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2', 
           'xmlns__sts': 'dian:gov:co:facturaelectronica:Structures-2-1', 
           'xmlns__xades': 'http://uri.etsi.org/01903/v1.3.2#', 
           'xmlns__xades141': 'http://uri.etsi.org/01903/v1.4.1#', 
           'xmlns__xsi': 'http://www.w3.org/2001/XMLSchema-instance', 
           'xsi__schemaLocation': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2 http://docs.oasis-open.org/ubl/os-UBL-2.1/xsd/maindoc/UBL-Invoice-2.1.xsd'})

        UBLExtensions = SubElement(Invoice, 'ext__UBLExtensions')
        self._cuds()
        self._rangos_ds(UBLExtensions)
        if self.journal_id.type_document_id.ecode == '20':
            if not self.einvice_form_payment_id:
                einvice_form_payment_id = self.env['form.payment.einvoice'].search([('code', '=', '1')], order="id asc", limit=1)
                self.write({'einvice_form_payment_id': einvice_form_payment_id.id})
            extennsion1 = SubElement(UBLExtensions, 'ext__UBLExtension')
            content1 = SubElement(extennsion1, 'ext__ExtensionContent')
            FabricanteSoftware = SubElement(content1, 'FabricanteSoftware')
            InformacionDelFabricanteDelSoftware = SubElement(FabricanteSoftware, 'InformacionDelFabricanteDelSoftware')
            SubElement(InformacionDelFabricanteDelSoftware, 'Name').text = 'NombreApellido'
            SubElement(InformacionDelFabricanteDelSoftware, 'Value').text = 'Juan Perez'
            SubElement(InformacionDelFabricanteDelSoftware, 'Name').text = 'RazonSocial'
            SubElement(InformacionDelFabricanteDelSoftware, 'Value').text = 'Empresa de software S.A.S'
            SubElement(InformacionDelFabricanteDelSoftware, 'Name').text = 'NombreSoftware'
            SubElement(InformacionDelFabricanteDelSoftware, 'Value').text = 'Nombre de la Aplicacion'

            extennsion3 = SubElement(UBLExtensions, 'ext__UBLExtension')
            content3 = SubElement(extennsion3, 'ext__ExtensionContent')
            BeneficiosComprador = SubElement(content3, 'BeneficiosComprador')
            InformacionBeneficiosComprador = SubElement(BeneficiosComprador, 'InformacionBeneficiosComprador')
            SubElement(InformacionBeneficiosComprador, 'Name').text = 'Codigo'
            SubElement(InformacionBeneficiosComprador, 'Value').text = '49'        
            SubElement(InformacionBeneficiosComprador, 'Name').text = 'NombresApellidos'
            SubElement(InformacionBeneficiosComprador, 'Value').text = 'JOHN DOE'        
            SubElement(InformacionBeneficiosComprador, 'Name').text = 'Puntos'
            SubElement(InformacionBeneficiosComprador, 'Value').text = '0' 

            extennsion4 = SubElement(UBLExtensions, 'ext__UBLExtension')
            content4 = SubElement(extennsion4, 'ext__ExtensionContent')
            PuntoVenta = SubElement(content4, 'PuntoVenta')
            InformacionCajaVenta = SubElement(PuntoVenta, 'InformacionCajaVenta')
            SubElement(InformacionCajaVenta, 'Name').text = 'PlacaCaja'
            SubElement(InformacionCajaVenta, 'Value').text = 'numero-de-placa1'        
            SubElement(InformacionCajaVenta, 'Name').text = 'UbicaciónCaja'
            SubElement(InformacionCajaVenta, 'Value').text = 'Ubicacion de la Caja 1'
            SubElement(InformacionCajaVenta, 'Name').text = 'Cajero'
            SubElement(InformacionCajaVenta, 'Value').text = 'Nombre de usuario'        
            SubElement(InformacionCajaVenta, 'Name').text = 'TipoCaja'
            SubElement(InformacionCajaVenta, 'Value').text = 'Tipo de Caja'        
            SubElement(InformacionCajaVenta, 'Name').text = 'CódigoVenta'
            SubElement(InformacionCajaVenta, 'Value').text = '179230'        
            SubElement(InformacionCajaVenta, 'Name').text = 'SubTotal'
            SubElement(InformacionCajaVenta, 'Value').text = '2000.00'

        extennsion2 = SubElement(UBLExtensions, 'ext__UBLExtension')
        content2 = SubElement(extennsion2, 'ext__ExtensionContent')


        SubElement(Invoice, 'cbc__UBLVersionID').text = 'UBL 2.1'
        operation_ds = self.env['type.operation.ds'].search([('code', '=', '10')], order="id asc", limit=1)
        if not self.partner_id.type_operation_ds.code:
            if not operation_ds:
                raise ValidationError('Debe configurar en el Cliente %s el tipo de operación' % (
                    self.partner_id.type_operation_ds.name,))

        if operation_ds:
            SubElement(Invoice, 'cbc__CustomizationID').text = operation_ds.code
        else:
            SubElement(Invoice, 'cbc__CustomizationID').text = self.partner_id.type_operation_ds.code
        if self.journal_id.type_document_id.ecode == '20':
            SubElement(Invoice, 'cbc__ProfileID').text = 'DIAN 2.1: Documento Equivalente POS'
            SubElement(Invoice, 'cbc__ProfileExecutionID').text = self.company_id.connection_pos_id.type
            SubElement(Invoice, 'cbc__ID').text = self.name
            if self.journal_id.type_document_id.ecode == '20':
                uuid = SubElement(Invoice, 'cbc__UUID', schemeID=self.company_id.connection_pos_id.type, schemeName='CUDE-SHA384')
            else:
                uuid = SubElement(Invoice, 'cbc__UUID', schemeID=self.company_id.connection_pos_id.type, schemeName='CUDS-SHA384')
        else:
            SubElement(Invoice, 'cbc__ProfileID').text = 'DIAN 2.1: documento soporte en adquisiciones efectuadas a no obligados a facturar.'
            SubElement(Invoice, 'cbc__ProfileExecutionID').text = self.company_id.connection_doc_sop_id.type
            SubElement(Invoice, 'cbc__ID').text = self.name
            if self.journal_id.type_document_id.ecode == '20':
                uuid = SubElement(Invoice, 'cbc__UUID', schemeID=self.company_id.connection_doc_sop_id.type, schemeName='CUDE-SHA384')
            else:
                uuid = SubElement(Invoice, 'cbc__UUID', schemeID=self.company_id.connection_doc_sop_id.type, schemeName='CUDS-SHA384')
        uuid.text = self.code_cuds
        formato = '%Y-%m-%d %H:%M:%S'
        tz = pytz.timezone('America/Bogota')
        fecha_factura = self.ds_date.replace(tzinfo=tz).strftime(formato)
        SubElement(Invoice, 'cbc__IssueDate').text = fecha_factura[:10]
        SubElement(Invoice, 'cbc__IssueTime').text = fecha_factura[11:] + '-05:00'
        SubElement(Invoice, 'cbc__DueDate').text = str(self.invoice_date_due)

        if self.journal_id.type_document_id.ecode == '20':
            itc = SubElement(Invoice, 'cbc__InvoiceTypeCode')
        else:
            itc = SubElement(Invoice, 'cbc__InvoiceTypeCode')
        
        if self.company_id.currency_id.id == self.currency_id.id:
            itc.text = str(self.journal_id.type_document_id.ecode)
        else:
            # itc.text = '95'
            itc.text = str(self.journal_id.type_document_id.ecode)

        SubElement(Invoice, 'cbc__Note').text = self.narration or ''
        SubElement(Invoice, 'cbc__DocumentCurrencyCode').text = self.currency_id.name
        line_count = self.env['account.move.line'].search([('move_id', '=', self.id),('exclude_from_invoice_tab', '=', False)])
        SubElement(Invoice, 'cbc__LineCountNumeric').text = str(len(line_count))

        self._party_supplier(Invoice)
        self._party_customer(Invoice)
        self._payment_means(Invoice)

        if self.company_id.currency_id.name != self.currency_id.name:
            self._PaymentExchangeRate(Invoice)

        # self._tax_totals(Invoice)
        self._tax_totals_ds(Invoice)
        lmt = SubElement(Invoice, 'cac__LegalMonetaryTotal')
        self._lmt(lmt)
        self._lineas_detalle_ds(Invoice)

        xmlstr = etree.tostring(Invoice, method='c14n').decode('utf8')
        xmlstr = xmlstr.replace('__', ':')
        
        invoice_signed = self.firmar_facturae(xmlstr)

        if not self.journal_id.type_document_id.sequence_id:
            raise ValidationError('¡Error! El tipo de documento no tiene una secuencia asignada. "%s"' % self.journal_id.type_document_id.name)
        seq = self.journal_id.type_document_id.sequence_id._next()
        consec = int(seq)
        # sequencia = hex(consec).split('x')[1].zfill(10)
        year = '24'
        ppp = '000'
        sequencia = hex(consec).split('x')[1].zfill(8)
        prefix = self.journal_id.type_document_id.code_prefix_file
        
        # archive_xml = prefix + self.company_id.partner_id.vat.zfill(10) + str(sequencia) + '.xml'
        if self.journal_id.type_document_id.ecode == '20':
            archive_xml = prefix + self.company_id.partner_id.vat.zfill(10) + ppp + year + str(sequencia) + '.xml'
        else:
            archive_xml = prefix + self.company_id.partner_id.vat.zfill(10) + str(sequencia) + '.xml'
        prefix = prefix.replace('face', 'ws')
        prefix_z = 'z'
        if self.journal_id.type_document_id.ecode == '20':
            archive_zip = prefix_z + self.company_id.partner_id.vat.zfill(10) + ppp + year + str(sequencia) + '.zip'
        else:
            archive_zip = prefix + self.company_id.partner_id.vat.zfill(10) + str(sequencia) + '.zip'
        self.filename_ds = archive_zip
        return (
         invoice_signed, archive_xml)

    def get_xml_ds_file(self):
        """
        Funcion para descargar el xml
        """
        return {'type': 'ir.actions.act_url',
                'url': ('/download/xml/enviods/{}').format(self.id),
                'target': 'self'}

    def get_status_validation_ds(self):
        self.ensure_one()
        values = {}
        if self.company_id.connection_doc_sop_id.type == '1':
            values['trackId'] = self.code_cuds
            XML_send = GetStatus['body']
            SOAP_action = GetStatus['action']
            WS_URL = self.company_id.connection_doc_sop_id.connection_url
        elif self.company_id.connection_doc_sop_id.type == '2':
            values['trackId'] = self.track_ds_id
            XML_send = GetStatusZip['body']
            SOAP_action = GetStatusZip['action']
            WS_URL = self.company_id.connection_doc_sop_id.connection_url
        else:
            return
        XML_send = XML_send % values
        self.send_ds(XML_send, SOAP_action, WS_URL)

    def _party_supplier(self, Invoice):
        partner_ds = self.partner_id

        if not partner_ds.x_document_type:
            raise ValidationError('El tipo de identificación %s no tiene código DIAN en el tercero de la compañía' % (
                partner_ds.x_document_type,))

        if not partner_ds.vat:
            raise ValidationError('El tercero de la compañía no tiene configurado el número de identificación %s ' % (
                partner_ds.name,))

        if partner_ds.x_digit_verification < 0 and not partner_ds.x_digit_verification:
            raise ValidationError('El tercero %s no presenta digito de velificacin' % (
                partner_ds.name,))

        asp = SubElement(Invoice, 'cac__AccountingSupplierParty')
        aac = SubElement(asp, 'cbc__AdditionalAccountID')
        aac.text = '1'
        party = SubElement(asp, 'cac__Party')
        pl = SubElement(party, 'cac__PhysicalLocation')
        addr = SubElement(pl, 'cac__Address')
        if not partner_ds.x_city:
            raise ValidationError('El tercero de la compañía no tiene configurado la ciudad %s ' % (
                partner_ds.name,))

        SubElement(addr, 'cbc__ID').text = partner_ds.x_city.code
        SubElement(addr, 'cbc__CityName').text = partner_ds.x_city.name

        if partner_ds.zip:
            SubElement(addr, 'cbc__PostalZone').text = partner_ds.zip or ''
        else:
            SubElement(addr, 'cbc__PostalZone').text = '000000'

        SubElement(
            addr, 'cbc__CountrySubentity').text = partner_ds.x_city.state_id.name
        SubElement(
            addr, 'cbc__CountrySubentityCode').text = partner_ds.state_id.code

        addrl = SubElement(addr, 'cac__AddressLine')
        if not partner_ds.street and not partner_ds.street2:
            raise ValidationError('El tercero de la compañía no tiene configurada una dirección %s ' % (
                partner_ds.name,))
        if partner_ds.street:
            SubElement(addrl, 'cbc__Line').text = partner_ds.street
        if partner_ds.street2 and not partner_ds.street:
            SubElement(addrl, 'cbc__Line').text = partner_ds.street2
        
        addrc = SubElement(addr, 'cac__Country')
        if not partner_ds.country_id:
            raise ValidationError('El tercero de la compañía no tiene configurado el país %s ' % (
                partner_ds.name,))

        SubElement(
            addrc, 'cbc__IdentificationCode').text = partner_ds.country_id and partner_ds.country_id.code or ''
        SubElement(addrc, 'cbc__Name', attrib={
                   'languageID': 'es'}).text = partner_ds.country_id.name

        pts = SubElement(party, 'cac__PartyTaxScheme')
        SubElement(pts, 'cbc__RegistrationName').text = partner_ds.name
        if not partner_ds.x_document_type:
            raise ValidationError(u'El tipo de documento %s no presenta código de DIAN' % (
                partner_ds.x_document_type,))

        SubElement(pts, 'cbc__CompanyID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}, schemeID=str(
            partner_ds.x_digit_verification), schemeName=self.company_id.partner_id.x_document_type).text = partner_ds.vat
        obligaciones = ''
        for obl in partner_ds.x_tax_responsibilities:
            if obligaciones == '':
                obligaciones = obl.code
            else:
                obligaciones = obligaciones + ',' + obl.code
        if not partner_ds.x_tax_responsibilities:
            raise ValidationError(u'El tercero %s no presenta responsabilidades fiscales' % (
                partner_ds.name,))
        print('OBLIGACIONES TRIBUTARIAS', obligaciones)
        SubElement(pts, 'cbc__TaxLevelCode',
                   listName='05' or '').text = obligaciones
        tax_scheme = SubElement(pts, 'cac__TaxScheme')
        SubElement(tax_scheme, 'cbc__ID').text = 'ZZ'
        SubElement(tax_scheme, 'cbc__Name').text = 'No aplica'

    def _party_customer(self, Invoice):
        partner = self.company_id.partner_id
        if partner.x_digit_verification < 0 and not partner.x_digit_verification:
            raise ValidationError(u'El tercero %s no presenta digito de velificacin' % (
                partner.name,))

        if not partner.x_document_type:
            raise ValidationError('El tipo de identificación %s no tiene código DIAN en el cliente' % (
                partner.x_document_type,))

        if not partner.vat:
            raise ValidationError('El cliente no tiene configurado el número de identificación %s ' % (
                partner.name,))

        asp = SubElement(Invoice, 'cac__AccountingCustomerParty')
        aac = SubElement(asp, 'cbc__AdditionalAccountID')
        if partner.company_type == 'person':
            type_company = '2'
        else:
            type_company = '1'
        aac.text = type_company
        aac.text = '1'
        party = SubElement(asp, 'cac__Party')

        pts = SubElement(party, 'cac__PartyTaxScheme')
        # if not partner.property_account_position_id and self.company_id.currency_id.id == self.currency_id.id:
        #     raise ValidationError(u'El cliente %s no presenta un re9gimen asociado' % (
        #         partner.name,))

        if not partner.x_tax_responsibilities and self.company_id.currency_id.id == self.currency_id.id:
            raise ValidationError(u'El tercero %s no presenta responsabilidades fiscales' % (
                partner.name,))

        SubElement(pts, 'cbc__RegistrationName').text = partner.name
        SubElement(pts, 'cbc__CompanyID', attrib={'schemeAgencyID': '195', 'schemeAgencyName': 'CO, DIAN (Dirección de Impuestos y Aduanas Nacionales)'}, schemeID=str(
            partner.x_digit_verification) or '', schemeName=partner.x_document_type).text = partner.vat
        obligaciones = ''
        for obl in partner.x_tax_responsibilities:
            if obligaciones == '':
                obligaciones = obl.code
            else:
                obligaciones = obligaciones + ',' + obl.code
        print('OBLIGACIONES TRIBUTARIAS', obligaciones)
        SubElement(pts, 'cbc__TaxLevelCode',
                   listName='05' or '').text = obligaciones

        tax_scheme = SubElement(pts, 'cac__TaxScheme')
        SubElement(tax_scheme, 'cbc__ID').text = '01'
        SubElement(tax_scheme, 'cbc__Name').text = 'IVA'

    def _payment_means(self, Invoice):
        invoice_payment_term_id = self.env['account.payment.term'].search([('einvice_form_payment_id.type', '=', '1')], order="id asc", limit=1)
        self.write({'invoice_payment_term_id': invoice_payment_term_id.id})
        if not self.invoice_payment_term_id:
            if not invoice_payment_term_id:
                raise ValidationError(u'La factura %s no tiene plazo de pago' % (
                    self.name or '',))
        if not self.einvice_payment_id:
            einvice_payment_id = self.env['mode.payment.einvoice'].search([('code', '=', '1')], order="id asc", limit=1)
            if not einvice_payment_id:
                raise ValidationError(u'La factura %s no tiene medio de pago segfan listado de la DIAN' % (
                    self.name or '',))
            else:
                self.write({'einvice_payment_id': einvice_payment_id.id})
        if not self.invoice_payment_term_id.einvice_form_payment_id:
            einvice_form_payment_id = self.env['form.payment.einvoice'].search([('code.type', '=', '1')], order="id asc", limit=1)
            self.write({'invoice_payment_term_id.einvice_form_payment_id': einvice_form_payment_id.id})
            if not einvice_form_payment_id:
                raise ValidationError(u'La factura %s no tiene una forma de pago según listado de la DIAN' % (
                    self.name or '',))
        if self.invoice_payment_term_id and self.invoice_payment_term_id.einvice_form_payment_id and self.invoice_payment_term_id.einvice_form_payment_id.code:
            payment_id = self.invoice_payment_term_id.einvice_form_payment_id.code

        payment_means = SubElement(Invoice, 'cac__PaymentMeans')
        SubElement(payment_means, 'cbc__ID').text = payment_id
        SubElement(payment_means,
                   'cbc__PaymentMeansCode').text = self.einvice_payment_id.code
        if not self.invoice_date_due:
            raise ValidationError('La factura %s no tiene fecha de vencimiento, por favor defina una fecha' % (
                self.name or '',))
        SubElement(payment_means, 'cbc__PaymentDueDate').text = str(
            self.invoice_date_due)
        SubElement(payment_means, 'cbc__PaymentID').text = '1234'

    def send_xml_ds(self):
        self.ensure_one()
        values = {}
        if self.journal_id.type_document_id.ecode == '20':
            if self.company_id.connection_pos_id.type == '1':
                XML_send = SendBillSync['body']
                SOAP_action = SendBillSync['action']
                WS_URL = self.company_id.connection_pos_id.connection_url
            elif self.company_id.connection_pos_id.type == '2':
                XML_send = SendTestSetAsync['body']
                SOAP_action = SendTestSetAsync['action']
                WS_URL = self.company_id.connection_pos_id.connection_url
            else:
                return
        else:
            if self.company_id.connection_doc_sop_id.type == '1':
                XML_send = SendBillSync['body']
                SOAP_action = SendBillSync['action']
                WS_URL = self.company_id.connection_doc_sop_id.connection_url
            elif self.company_id.connection_doc_sop_id.type == '2':
                XML_send = SendTestSetAsync['body']
                SOAP_action = SendTestSetAsync['action']
                WS_URL = self.company_id.connection_doc_sop_id.connection_url
            else:
                return

        sio = BytesIO()
        #sio = io.StringIO()
        zf = ZipFile(sio, 'a')
        zf.writestr(self.ds_name, self.xml_ds_document.encode('UTF-8'))
        zf.close()
        sio.seek(0)
        file_zip = sio.getvalue()
        document_b64 = base64.b64encode(file_zip).decode('UTF-8')
        #document_b64 = base64.b64encode(file_zip).decode('UTF-8')
        #self.file_zip_ds = file_zip
        values['zip_fileName'] = self.filename_ds
        values['zip_data'] = document_b64
        values['TestSetId'] = self.company_id.connection_doc_sop_id.test_set_id
        XML_send = XML_send % values
        _logger.warning('******* send_ds SOAP_ACTION %s WS_URL %s' % (SOAP_action,WS_URL))
        self.send_ds(XML_send, SOAP_action, WS_URL)

    def send_ds(self, xml_send, soap_action, ws_url):
        xml_sign = self.sign_SOAP(xml_send, soap_action)
        headers = {'Accept': 'application/xml', 
           'Content-type': 'application/soap+xml;charset=UTF-8', 
           'Content-length': str(len(xml_sign.decode('UTF-8')))}
        response = requests.post(url=ws_url, data=xml_sign.decode('UTF-8'), headers=headers)
        self.xml_envio_ds = response.request.body

        xmldoc = minidom.parseString((response.text).encode('utf-8'))
        if response.ok:
            for line in self.bug_ds_ids:
                if line.type == 'response':
                    line.unlink()
            if self.journal_id.type_document_id.ecode == '20':
                if self.company_id.connection_pos_id.type == '2':
                    if xmldoc.getElementsByTagName('c:Success') and xmldoc.getElementsByTagName('c:Success')[0].firstChild.nodeValue == 'false':
                        self.state_doc_sop = 'error'
                        self.dian_receipt_ds = xmldoc.getElementsByTagName('c:ProcessedMessage')[0].firstChild.nodeValue

                    if xmldoc.getElementsByTagName('b:ZipKey') and not xmldoc.getElementsByTagName('c:ProcessedMessage'):
                        self.track_ds_id = xmldoc.getElementsByTagName('b:ZipKey')[0].firstChild.nodeValue
                        self.state_doc_sop = 'send'
                        self.dian_receipt_ds = 'Documento enviado para validaciones'

                    if xmldoc.getElementsByTagName('GetStatusZipResponse'):
                        if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'false':
                            self.state_doc_sop = 'error'
                            if xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild:
                                self.dian_receipt_ds = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                                errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                                for node in errores.childNodes:
                                    line = node.firstChild.nodeValue.split(',')
                                    self.env['eresponse.bugs'].create({'send_ds_id': self.id, 
                                    'type': 'response', 
                                    'code': line[0].replace('Regla: ', ''), 
                                    'description': line[1]})
                            elif xmldoc.getElementsByTagName('b:StatusDescription'):
                                for elem in xmldoc.getElementsByTagName('b:StatusDescription'):
                                    self.dian_receipt_ds = elem.firstChild.data

                        if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'true':
                            self.state_doc_sop = 'done'
                            for line in self.bug_ds_ids:
                                if line.type == 'response':
                                    line.unlink()

                            self.dian_receipt_ds = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                            filename = self.ds_name + '.xml'
                            data = self.xml_ds_document
                            data_attach = {'name': filename, 
                            'datas': data and base64.encodestring(bytes(bytearray(data, encoding='utf-8'))) or None, 
                            'store_fname': filename, 
                            'description': 'Factura-E XML ' + self.name, 
                            'res_model': 'account.move', 
                            'res_id': self.id}
                            attachment_id_xml = self.env['ir.attachment'].sudo().create(data_attach)
                if self.company_id.connection_pos_id.type == '1':
                    xml_response = etree.fromstring(response.text)
                    IsValid = xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.data == 'true'
                    StatusMessage = xmldoc.getElementsByTagName('b:StatusMessage') and xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.data
                    StatusDescription = xmldoc.getElementsByTagName('b:StatusDescription') and xmldoc.getElementsByTagName('b:StatusDescription')[0].firstChild.data
                    # XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild.data
                    XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild
                    if IsValid:
                        if self.journal_id.type_document_id.ecode == '20':
                            self.state_doc_sop = 'done'
                            self.state_dian_document = 'done'
                            self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cuds
                            self.einvoice_document.state = 'done'
                        else:
                            self.state_doc_sop = 'done'
                            self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cuds
                            
                    else:
                        self.state_doc_sop = 'error'
                    self.dian_receipt_ds = StatusDescription
                    self.track_ds_id = XmlDocumentKey
                    if xmldoc.getElementsByTagName('b:ErrorMessage')[0].firstChild:
                        errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                        for node in errores.childNodes:
                            line = node.firstChild.nodeValue.split(',')
                            if line[0] and line[0]=='Regla: 90':
                                XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild.data
                                self.state_doc_sop = 'done'
                                self.write({'code_cuds': XmlDocumentKey})
                                self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + XmlDocumentKey
                                self.dian_receipt_ds = 'Procesado Correctamente.'
                            else:
                                self.env['eresponse.bugs'].create({'send_ds_id': self.id, 
                                'type': 'response', 
                                'code': line[0].replace('Regla: ', ''), 
                                'description': line[1]})
            else:
                if self.company_id.connection_doc_sop_id.type == '2':
                    if xmldoc.getElementsByTagName('c:Success') and xmldoc.getElementsByTagName('c:Success')[0].firstChild.nodeValue == 'false':
                        self.state_doc_sop = 'error'
                        self.dian_receipt_ds = xmldoc.getElementsByTagName('c:ProcessedMessage')[0].firstChild.nodeValue

                    if xmldoc.getElementsByTagName('b:ZipKey') and not xmldoc.getElementsByTagName('c:ProcessedMessage'):
                        self.track_ds_id = xmldoc.getElementsByTagName('b:ZipKey')[0].firstChild.nodeValue
                        self.state_doc_sop = 'send'
                        self.dian_receipt_ds = 'Documento enviado para validaciones'

                    if xmldoc.getElementsByTagName('GetStatusZipResponse'):
                        if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'false':
                            self.state_doc_sop = 'error'
                            if xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild:
                                self.dian_receipt_ds = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                                errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                                print('ERRORES', errores)
                                for node in errores.childNodes:
                                    line = node.firstChild.nodeValue.split(',')
                                    self.env['eresponse.bugs'].create({'send_ds_id': self.id, 
                                    'type': 'response', 
                                    'code': line[0].replace('Regla: ', ''), 
                                    'description': line[1]})
                            elif xmldoc.getElementsByTagName('b:StatusDescription'):
                                for elem in xmldoc.getElementsByTagName('b:StatusDescription'):
                                    self.dian_receipt_ds = elem.firstChild.data

                        if xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.nodeValue == 'true':
                            self.state_doc_sop = 'done'
                            for line in self.bug_ds_ids:
                                if line.type == 'response':
                                    line.unlink()

                            self.dian_receipt_ds = xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.nodeValue
                            filename = self.ds_name + '.xml'
                            data = self.xml_ds_document
                            data_attach = {'name': filename, 
                            'datas': data and base64.encodestring(bytes(bytearray(data, encoding='utf-8'))) or None, 
                            'store_fname': filename, 
                            'description': 'Factura-E XML ' + self.name, 
                            'res_model': 'account.move', 
                            'res_id': self.id}
                            attachment_id_xml = self.env['ir.attachment'].sudo().create(data_attach)
                if self.company_id.connection_doc_sop_id.type == '1':
                    xml_response = etree.fromstring(response.text)
                    IsValid = xmldoc.getElementsByTagName('b:IsValid') and xmldoc.getElementsByTagName('b:IsValid')[0].firstChild.data == 'true'
                    StatusMessage = xmldoc.getElementsByTagName('b:StatusMessage') and xmldoc.getElementsByTagName('b:StatusMessage')[0].firstChild.data
                    StatusDescription = xmldoc.getElementsByTagName('b:StatusDescription') and xmldoc.getElementsByTagName('b:StatusDescription')[0].firstChild.data
                    # XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild.data
                    XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild
                    if IsValid:
                        if self.journal_id.type_document_id.ecode == '20':
                            self.state_doc_sop = 'done'
                            self.state_dian_document = 'done'
                            self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cuds
                            self.einvoice_document.state = 'done'
                        else:
                            self.state_doc_sop = 'done'
                            self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + self.code_cuds
                            
                    else:
                        self.state_doc_sop = 'error'
                    self.dian_receipt_ds = StatusDescription
                    self.track_ds_id = XmlDocumentKey
                    if xmldoc.getElementsByTagName('b:ErrorMessage')[0].firstChild:
                        errores = xmldoc.getElementsByTagName('b:ErrorMessage')[0]
                        for node in errores.childNodes:
                            line = node.firstChild.nodeValue.split(',')
                            if line[0] and line[0]=='Regla: 90':
                                XmlDocumentKey = xmldoc.getElementsByTagName('b:XmlDocumentKey') and xmldoc.getElementsByTagName('b:XmlDocumentKey')[0].firstChild.data
                                self.state_doc_sop = 'done'
                                self.write({'code_cuds': XmlDocumentKey})
                                self.url_dian_ds = 'https://catalogo-vpfe.dian.gov.co/document/searchqr?documentkey=' + XmlDocumentKey
                                self.dian_receipt_ds = 'Procesado Correctamente.'
                            else:
                                self.env['eresponse.bugs'].create({'send_ds_id': self.id, 
                                'type': 'response', 
                                'code': line[0].replace('Regla: ', ''), 
                                'description': line[1]})
        else:
            self.state_doc_sop = 'error'
            self.dian_receipt_ds = 'El servicio web no responde correctamente. C\xc3\xb3digo respuesta ' + str(response.status_code)

    def _tax_totals_ds(self, invoice):
        id = 1
        code = False
        TaxAmount = None
        amount = 0.0
        for tax_line in self.line_ids:
            if tax_line.tax_line_id and not tax_line.tax_group_id.tributo_id.code:
                continue
                # raise ValidationError(u'El impuesto %s no presenta cdigo de impuesto DIAN' % (
                #     tax_line.tax_line_id.name,))
            if tax_line.tax_group_id.tributo_id.code == '07':
                continue
            if tax_line.tax_line_id and tax_line.tax_group_id:
                if tax_line.tax_group_id and not tax_line.tax_group_id.tributo_id.code:
                    continue
                    # raise ValidationError(u'El impuesto %s no presenta cdigo de impuesto DIAN' % (
                    #     tax_line.tax_line_id.name,))
                amount = 0.0
                if tax_line.tax_group_id.tributo_id.code in ('05', '06', '07'):
                    tax_total = SubElement(invoice, 'cac__WithholdingTaxTotal')
                    amount = amount + round(abs(tax_line.debit), 2)
                else:
                    tax_total = SubElement(invoice, 'cac__TaxTotal')
                    amount = amount + round(abs(tax_line.credit), 2)
                # if TaxAmount != None:
                #     TaxAmount.text = str('%.2f' % amount)
                # else:
                TaxAmount = SubElement(tax_total, 'cbc__TaxAmount', attrib={
                                        'currencyID': tax_line.move_id.currency_id.name})
                # TaxAmount.text = str('%.2f' % round(amount, 2))

                ts = SubElement(tax_total, 'cac__TaxSubtotal')
                SubElement(ts, 'cbc__TaxableAmount', attrib={'currencyID': tax_line.move_id.currency_id.name}).text = str(
                    '%.2f' % round(abs(tax_line.tax_base_amount), 2))
                if tax_line.credit > 0.0:
                    SubElement(ts, 'cbc__TaxAmount', attrib={'currencyID': tax_line.move_id.currency_id.name}).text = str(
                        '%.2f' % round(abs(tax_line.credit), 2))
                    TaxAmount.text = str('%.2f' % round(abs(tax_line.credit), 2))
                else:
                    SubElement(ts, 'cbc__TaxAmount', attrib={'currencyID': tax_line.move_id.currency_id.name}).text = str(
                        '%.2f' % round(abs(tax_line.debit), 2))
                    TaxAmount.text = str('%.2f' % round(abs(tax_line.debit), 2))
                tc = SubElement(ts, 'cac__TaxCategory')
                SubElement(tc, 'cbc__Percent').text = str("%.2f" %
                                                          float(abs(tax_line.tax_line_id.amount)))
                tsc = SubElement(tc, 'cac__TaxScheme')
                SubElement(
                    tsc, 'cbc__ID').text = tax_line.tax_group_id.tributo_id.code
                SubElement(
                    tsc, 'cbc__Name').text = tax_line.tax_group_id.tributo_id.name
                code = tax_line.tax_group_id.code
        return

    def _lmt(self, lmt):
        SubElement(lmt, 'cbc__LineExtensionAmount', attrib={
                   'currencyID': self.currency_id.name}).text = str('%.2f' % round(self.amount_untaxed, 2))
        amount_untaxed = self.amount_untaxed
        tax_total = 0.0
        base_total = 0.0
        for line_tax in self.line_ids:
            if not line_tax.tax_line_id:
                continue
            if line_tax.tax_group_id and not line_tax.tax_group_id.tributo_id.code:
                continue
                # raise ValidationError(u'El impuesto %s no presenta cdigo de impuesto DIAN' % (
                #     line_tax.tax_line_id.name,))
            if line_tax.tax_group_id.tributo_id.code in ('01',):
                tax_total += line_tax.credit
                base_total += line_tax.tax_base_amount
        TaxExclusiveAmount = base_total
        TaxInclusiveAmount = amount_untaxed + tax_total
        SubElement(lmt, 'cbc__TaxExclusiveAmount', attrib={
                   'currencyID': self.currency_id.name}).text = str('%.2f' % round(TaxExclusiveAmount, 2))
        SubElement(lmt, 'cbc__TaxInclusiveAmount', attrib={
                   'currencyID': self.currency_id.name}).text = str('%.2f' % round(TaxInclusiveAmount, 2))
        SubElement(lmt, 'cbc__PrepaidAmount', attrib={
                   'currencyID': self.currency_id.name}).text = str('%.2f' % round(0, 2))
        SubElement(lmt, 'cbc__PayableAmount', attrib={
                   'currencyID': self.currency_id.name}).text = str('%.2f' % round(TaxInclusiveAmount, 2))

    def _lineas_detalle_ds(self, Invoice):
        line_number = 1
        discount_line = 1
        tax_fe=1        
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.invoice_date)
        # self.action_post_taxes()
        for line_invoice in self.invoice_line_ids:
            qty = round(line_invoice.quantity, 4)
            line = SubElement(Invoice, 'cac__InvoiceLine')
            no_product = False
            if line_invoice.product_id.default_code == 'NO_PRODUCT':
                no_product = True
            SubElement(line, 'cbc__ID').text = str(line_number)

            formato = '%Y-%m-%d %H:%M:%S'
            tz = pytz.timezone('America/Bogota')
            fecha_factura = self.ds_date.replace(tzinfo=tz).strftime(formato)
            SubElement(line, 'cbc__Note').text = line_invoice.name or ''
            SubElement(line, 'cbc__InvoicedQuantity', unitCode='NIU').text = str(qty)
            SubElement(line, 'cbc__LineExtensionAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % round(line_invoice.price_subtotal, 1))
            if self.journal_id.type_document_id.ecode != '20':
                InvoicePeriod = SubElement(line, 'cac__InvoicePeriod')
                SubElement(InvoicePeriod, 'cbc__StartDate').text = fecha_factura[:10]
                form_send_ds_id = self.env['form.send.ds'].search([('code', '=', '1')], order="id asc", limit=1)
                if not self.form_send_ds_id:
                    if form_send_ds_id:
                        self.write({'form_send_ds_id': form_send_ds_id.id})
                    else:    
                        raise ValidationError('¡Error! Debe configurar la Forma de generación y transmisión en el documento. "%s"' % self.name)
                SubElement(InvoicePeriod, 'cbc__DescriptionCode').text = self.form_send_ds_id.code
                SubElement(InvoicePeriod, 'cbc__Description').text = self.form_send_ds_id.name

            if line_invoice.discount != 0:
                price_unit = line_invoice.price_unit * (1 - (line_invoice.discount or 0.0) / 100.0)
                total_discount = round(line_invoice.price_unit * line_invoice.discount / 100.0 * line_invoice.quantity, 2)
                base_discount = round(line_invoice.price_unit * line_invoice.quantity, 2)
                allowancecharge = SubElement(line, 'cac__AllowanceCharge')
                SubElement(allowancecharge, 'cbc__ID').text = str(discount_line)
                SubElement(allowancecharge, 'cbc__ChargeIndicator').text = 'false'
                SubElement(allowancecharge, 'cbc__AllowanceChargeReason').text = 'Descuento por cliente frecuente'
                SubElement(allowancecharge, 'cbc__MultiplierFactorNumeric').text = str('%.2f' % round(line_invoice.discount, 2))
                SubElement(allowancecharge, 'cbc__Amount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % round(total_discount, 2))
                SubElement(allowancecharge, 'cbc__BaseAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % round(base_discount, 2))
                discount_line = discount_line + 1
            price_unit = line_invoice.price_unit * (1 - (line_invoice.discount or 0.0) / 100.0)
            # taxes = line_invoice.invoice_line_tax_ids.compute_all(price_unit, self.invoice_id.currency_id, line_invoice.quantity, product=line_invoice.product_id, partner=line_invoice.move_id.partner_id)['taxes']
            # tax_key = []
            # for line_tax in self.invoice_id.tax_line_ids:
            #     tax_key.append(line_tax.tax_id.id)

            # taxes_id = self.env['move.line.tax'].search([('line_id', '=', line_invoice.id)], order="id asc")
            # if taxes_id:
            #     for i in range(2):
            #         for tax in taxes_id:
            #             if tax.tax_id.tax_group_id.tributo_id.code == '07':
            #                 continue
            #             if not tax.tax_id.tax_group_id:
            #                 continue
            #             if not tax.tax_id.tax_group_id.tributo_id:
            #                 continue
            #             round_curr = self.currency_id.round
            #             if i == 0:
            #                 if tax.tax_id.tax_group_id.tributo_id.code in ('05', '06', '07'):
            #                     continue
            #             if i == 1:
            #                 #if tax.tax_id.tax_group_id.tributo_id.code not in ('05', '06'):
            #                 if tax.tax_id.tax_group_id.tributo_id.code not in ('05', '06', '07'):
            #                     continue
            #             val_amount = round(abs(tax.amount), 2)
            #             if tax.tax_id.tax_group_id.tributo_id.code in ('07'):
            #                 val_amount = round(abs(tax.amount), 3)
            #             if tax.tax_id.tax_group_id.tributo_id.code in ('05', '06', '07'):
            #                 taxtotal = SubElement(line, 'cac__WithholdingTaxTotal')
            #             else:
            #                 taxtotal = SubElement(line, 'cac__TaxTotal')
            #             if abs(tax.amount) > 0.0:
            #                 SubElement(taxtotal, 'cbc__TaxAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % val_amount)
            #             tax_subtotal = SubElement(taxtotal, 'cac__TaxSubtotal')
            #             SubElement(tax_subtotal, 'cbc__TaxableAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % round(tax.base, 2))
            #             if abs(tax.amount) > 0.0:
            #                 SubElement(tax_subtotal, 'cbc__TaxAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str('%.2f' % val_amount)
            #             tax_category = SubElement(tax_subtotal, 'cac__TaxCategory')
            #             v_amount = tax.tax_id.amount 
            #             if tax.tax_id.tax_group_id.tributo_id.code in ('05', '06', '07'):
            #                 SubElement(tax_category, 'cbc__Percent').text = str("%.3f" % float(abs(v_amount)))
            #             else:
            #                 SubElement(tax_category, 'cbc__Percent').text = str("%.2f" % float(abs(v_amount)))
            #             tax_scheme = SubElement(tax_category, 'cac__TaxScheme')
            #             SubElement(tax_scheme, 'cbc__ID').text = tax.tax_id.tax_group_id.tributo_id.code or ''
            #             SubElement(tax_scheme, 'cbc__Name').text = tax.tax_id.tax_group_id.tributo_id.name or ''



            item = SubElement(line, 'cac__Item')
            SubElement(item, 'cbc__Description').text = self._acortar_str(line_invoice.name, 1000)
            seller_item = SubElement(item, 'cac__SellersItemIdentification')
            SubElement(seller_item, 'cbc__ID')
            
            StandardItemIdentification = SubElement(item, 'cac__StandardItemIdentification')
            SubElement(StandardItemIdentification, 'cbc__ID', attrib={'schemeID': '999', 'schemeName': 'Estándar de adopción del contribuyente'}).text = '123455'

            item_identificaction = SubElement(item, 'cac__AdditionalItemIdentification')
            SubElement(item_identificaction, 'cbc__ID')
            price = SubElement(line, 'cac__Price')
            SubElement(price, 'cbc__PriceAmount', attrib={'currencyID': line_invoice.move_id.currency_id.name}).text = str(round(line_invoice.price_unit, 6))
            SubElement(price, 'cbc__BaseQuantity', unitCode='NIU').text = str(qty)
            line_number = line_number + 1

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
            sign = xmlsig.template.create(c14n_method=xmlsig.constants.TransformInclC14N,
                                          sign_method=xmlsig.constants.TransformRsaSha256, name=signature_id, ns='ds')
            key_info = xmlsig.template.ensure_key_info(sign, name=key_info_id)
            x509_data = xmlsig.template.add_x509_data(key_info)
            xmlsig.template.x509_data_add_certificate(x509_data)
            p12 = crypto.load_pkcs12(base64.decodestring(
                self.company_id.connection_doc_sop_id.certificate_id.cert_file), self.company_id.connection_doc_sop_id.certificate_id.cert_pass)
            priv_key = crypto.dump_privatekey(
                crypto.FILETYPE_PEM, p12.get_privatekey())
            certificate1 = p12.get_certificate()
            certificate1_pem = crypto.dump_certificate(
                crypto.FILETYPE_PEM, p12.get_certificate())
            ref = xmlsig.template.add_reference(
                sign, xmlsig.constants.TransformSha256, name=reference_id, uri=None)
            xmlsig.template.add_reference(
                sign, xmlsig.constants.TransformSha256, uri='#' + key_info_id)
            xmlsig.template.add_reference(sign, xmlsig.constants.TransformSha256, uri='#' +
                                          signed_properties_id, uri_type='http://uri.etsi.org/01903#SignedProperties')
            xmlsig.template.add_transform(
                ref, xmlsig.constants.TransformEnveloped)
            object_node = etree.SubElement(
                sign, etree.QName(xmlsig.constants.DSigNs, 'Object'))
            qualifying_properties = etree.SubElement(object_node, etree.QName(xades, 'QualifyingProperties'), nsmap={
                                                     'xades': xades, 'xades141': 'http://uri.etsi.org/01903/v1.4.1#'}, attrib={'Target': '#' + signature_id})
            signed_properties = etree.SubElement(qualifying_properties, etree.QName(
                xades, 'SignedProperties'), attrib={'Id': signed_properties_id})
            signed_signature_properties = etree.SubElement(
                signed_properties, etree.QName(xades, 'SignedSignatureProperties'))
            now = datetime.now()
            fecha_actual = now.isoformat()
            formato = '%Y-%m-%dT%H:%M:%S'
            tz = pytz.timezone('America/Bogota')
            fecha_envio = datetime.now(tz).strftime(formato)
            fecha_envio = fecha_envio + '-05:00'
            # self.write({'signingtime': fecha_actual})
            etree.SubElement(signed_signature_properties, etree.QName(
                xades, 'SigningTime')).text = fecha_envio
            signing_certificate = etree.SubElement(
                signed_signature_properties, etree.QName(xades, 'SigningCertificate'))
            signing_certificate_cert1 = etree.SubElement(
                signing_certificate, etree.QName(xades, 'Cert'))
            cert_digest1 = etree.SubElement(
                signing_certificate_cert1, etree.QName(xades, 'CertDigest'))
            etree.SubElement(cert_digest1, etree.QName(
                xmlsig.constants.DSigNs, 'DigestMethod'), attrib={'Algorithm': algoritm})
            hash_cert1 = hashlib.sha256(crypto.dump_certificate(
                crypto.FILETYPE_ASN1, certificate1))
            etree.SubElement(cert_digest1, etree.QName(
                xmlsig.constants.DSigNs, 'DigestValue')).text = base64.b64encode(hash_cert1.digest())
            issuer_serial1 = etree.SubElement(
                signing_certificate_cert1, etree.QName(xades, 'IssuerSerial'))
            etree.SubElement(issuer_serial1, etree.QName(xmlsig.constants.DSigNs, 'X509IssuerName')
                             ).text = 'C=CO,L=Bogota D.C.,O=Andes SCD.,OU=Division de certificacion entidad final,CN=CA ANDES SCD S.A. Clase II,1.2.840.113549.1.9.1=#1614696e666f40616e6465737363642e636f6d2e636f'
            etree.SubElement(issuer_serial1, etree.QName(
                xmlsig.constants.DSigNs, 'X509SerialNumber')).text = str(certificate1.get_serial_number())
            signature_policy_identifier = etree.SubElement(
                signed_signature_properties, etree.QName(xades, 'SignaturePolicyIdentifier'))
            signature_policy_id = etree.SubElement(
                signature_policy_identifier, etree.QName(xades, 'SignaturePolicyId'))
            sig_policy_id = etree.SubElement(
                signature_policy_id, etree.QName(xades, 'SigPolicyId'))
            etree.SubElement(sig_policy_id, etree.QName(
                xades, 'Identifier')).text = sig_policy_identifier
            sig_policy_hash = etree.SubElement(
                signature_policy_id, etree.QName(xades, 'SigPolicyHash'))
            etree.SubElement(sig_policy_hash, etree.QName(
                xmlsig.constants.DSigNs, 'DigestMethod'), attrib={'Algorithm': algoritm})
            hash_value = sig_policy_hash_value
            etree.SubElement(sig_policy_hash, etree.QName(
                xmlsig.constants.DSigNs, 'DigestValue')).text = hash_value
            signer_role = etree.SubElement(
                signed_signature_properties, etree.QName(xades, 'SignerRole'))
            claimed_roles = etree.SubElement(
                signer_role, etree.QName(xades, 'ClaimedRoles'))
            etree.SubElement(claimed_roles, etree.QName(
                xades, 'ClaimedRole')).text = 'third party'
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

        tree = etree.fromstring(xml_facturae.encode(
            'utf-8'), etree.XMLParser(remove_blank_text=True, encoding='utf-8'))
        xml_facturae = etree.tostring(
            tree, xml_declaration=False, encoding='UTF-8').decode('utf8')
        cert = self.company_id.connection_doc_sop_id.certificate_id.cert_file
        cert_password = self.company_id.connection_doc_sop_id.certificate_id.cert_pass
        invoice_root = _sign_file(cert, cert_password, xml_facturae)
        invoice_signed = etree.tostring(
            invoice_root, xml_declaration=False, encoding='UTF-8').decode('utf8')
        signature = xmlstr = invoice_signed[invoice_signed.find(
            '<ds:Signature'):invoice_signed.find('</ds:Signature>') + 15]
        invoice_signed = invoice_signed.replace(signature, '')
        invoice_signed = invoice_signed.replace(
            '<ext:ExtensionContent/>', '<ext:ExtensionContent>' + signature + '</ext:ExtensionContent>')
        return invoice_signed

    def sign_SOAP(self, xml_send, soap_action):
        keyfile = self.company_id.connection_doc_sop_id.certificate_id.cert_file
        password = self.company_id.connection_doc_sop_id.certificate_id.cert_pass
        singing = Signing(keyfile, password)
        element = etree.fromstring(xml_send, parser=etree.XMLParser(
            recover=True, remove_blank_text=True))
        singner = SOAPSing(singing)
        soapSinged = singner.sing(element, soap_action)
        xml_sign = etree.tostring(soapSinged)
        return xml_sign
