# -*- coding: utf-8 -*-
    

from datetime import date
import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, ValidationError
import base64

import logging
_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
    type_ = crypto.FILETYPE_PEM
except ImportError:
    _logger.warning('Error en cargar crypto')    


class ECertificate(models.Model):
    _name = 'ecertificate'
    _description = "ECertificate"

    name = fields.Char('Name')
    date_start = fields.Datetime('Start Date')
    date_end = fields.Datetime('End Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('expired', 'Expired')
    ], required=True, string="Status", default='draft')
    cert_file = fields.Binary(string='PFX File', required=False, store=True, help='Upload the PFX File', filters='*.pfx')
    pem_file = fields.Binary(string='File PEM', required=False, store=True, help='Upload the PEM File')
    cert_pass = fields.Char('Password')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))
    certificate = fields.Char('Certificate')
    description = fields.Char('Description')
    issuer_name = fields.Char(string="Ente emisor del certificado", default="")
    serial_number = fields.Char(string="Serial del certificado", default="", required=True)
    issuer_organization = fields.Char(string='Issuer Organization', readonly=True)
    cert = fields.Text(string='Certificate', readonly=True)
    subject_c = fields.Char(string='Subject Country', readonly=True)
    subject_title = fields.Char(string='Subject Title', readonly=True)
    subject_common_name = fields.Char(string='Subject Common Name', readonly=True)
    subject_serial_number = fields.Char(string='Subject Serial Number')
    subject_email_address = fields.Char(string='Subject Email Address', readonly=True)
    issuer_country = fields.Char(string='Issuer Country', readonly=True)
    issuer_serial_number = fields.Char(string='Issuer Serial Number', readonly=True)
    issuer_email_address = fields.Char(string='Issuer Email Address', readonly=True)
    cert_serial_number = fields.Char(string='Serial Number', readonly=True)
    cert_signature_algor = fields.Char(string='Signature Algorithm', readonly=True)
    cert_version = fields.Char(string='Version', readonly=True)
    cert_hash = fields.Char(string='Hash', readonly=True)
    private_key_bits = fields.Char(string='Private Key Bits', readonly=True)
    private_key_check = fields.Char(string='Private Key Check', readonly=True)
    private_key_type = fields.Char(string='Private Key Type', readonly=True)
    priv_key = fields.Text(string='Private Key', readonly=True)

    def name_get(self):
        return [(cert.id, '%s - %s' % (cert.name, cert.date_end)) for cert in self]

    def load_cert_pk12(self, filecontent):
        p12 = crypto.load_pkcs12(filecontent, self.cert_pass)
        cert = p12.get_certificate()
        privky = p12.get_privatekey()
        issuer = cert.get_issuer()
        subject = cert.get_subject()
        self.date_start = datetime.datetime.strptime(cert.get_notBefore().decode('utf-8'), '%Y%m%d%H%M%SZ')
        self.date_end = datetime.datetime.strptime(cert.get_notAfter().decode('utf-8'), '%Y%m%d%H%M%SZ')
        self.subject_c = subject.C
        self.subject_title = subject.title
        self.name = subject.CN
        self.subject_common_name = subject.CN
        self.subject_serial_number = subject.serialNumber
        self.subject_email_address = subject.emailAddress
        self.issuer_country = issuer.C
        self.issuer_organization = issuer.O
        self.issuer_name = issuer.CN
        self.issuer_serial_number = issuer.serialNumber
        self.issuer_email_address = issuer.emailAddress
        self.state = 'expired' if cert.has_expired() else 'valid'
        self.cert_serial_number = cert.get_serial_number()
        self.cert_signature_algor = cert.get_signature_algorithm()
        self.cert_version = cert.get_version()
        self.cert_hash = cert.subject_name_hash()
        self.private_key_bits = privky.bits()
        self.private_key_check = privky.check()
        self.private_key_type = privky.type()
        certificate = p12.get_certificate()
        private_key = p12.get_privatekey()
        self.priv_key = crypto.dump_privatekey(type_, private_key)
        self.cert = crypto.dump_certificate(type_, certificate)

    def action_draft_cert(self):
        self.date_start = None
        self.date_end = None
        self.name = None
        self.cert_file = None
        self.cert_pass = None
        self.cert = None
        self.priv_key = None
        return self.write({'state': 'draft'})

    def action_valid_cert(self):
        self.ensure_one()
        if not self.cert_file:
            raise Warning(u'Certificado digital en formato PFX vacio')
        if not self.pem_file:
            raise Warning(u'Certificado digital en formato PEM vacio')
        if not self.cert_pass:
            raise Warning(u'Password vacio')
        filecontent = base64.b64decode(self.cert_file)
        self.load_cert_pk12(filecontent)
