# -*- coding: utf-8 -*-

import hashlib, uuid
from string import Template
import base64
from odoo.addons.edoc_sop_logyca.REQUESTDian.Utils import find_node
from odoo.addons.edoc_sop_logyca.REQUESTDian.SingNS import *
from lxml import etree
import datetime
from pytz import timezone
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO

envelope_template = Template('\n<${soap}:Envelope xmlns:${soap}="${soap_url}" xmlns:${wcf_env}="${wcf_env_url}">\n    <${soap}:Header xmlns:${wsa_env}="${wsa_env_url}">\n        <${wsse}:Security xmlns:${wsse}="${wsse_url}" xmlns:${wsu}="${wsu_url}">\n            <wsu:Timestamp wsu:Id="${timestam_id}">\n                <wsu:Created>${timestamp_created}</wsu:Created>\n                <wsu:Expires>${timestamp_expires}</wsu:Expires>\n            </wsu:Timestamp>\n            <${wsse}:BinarySecurityToken EncodingType="${encoding_base64_url}" ValueType="${value_x509_url}" ${wsu}:Id="${cert_id}">${sec_token}</${wsse}:BinarySecurityToken>\n            <${ds}:Signature Id="${sig_id}" xmlns:${ds}="${ds_url}">\n              <${ds}:SignedInfo>\n                 <${ds}:CanonicalizationMethod Algorithm="${ec_url}">\n                    <${ec}:InclusiveNamespaces xmlns:${ec}="${ec_url}" PrefixList="${soap} ${wsa_env} ${wcf_env}"/>\n                 </${ds}:CanonicalizationMethod>\n                 <${ds}:SignatureMethod Algorithm="${algo_sha256}"/>\n                 <${ds}:Reference URI="#${body_id}">\n                    <${ds}:Transforms>\n                       <${ds}:Transform Algorithm="${ec_url}">\n                          <${ec}:InclusiveNamespaces xmlns:${ec}="${ec_url}" PrefixList="${soap} ${wcf_env}"/>\n                       </${ds}:Transform>\n                    </${ds}:Transforms>\n                    <${ds}:DigestMethod Algorithm="${algo_digest_sha256}"/>\n                    <${ds}:DigestValue></${ds}:DigestValue>\n                 </${ds}:Reference>\n              </${ds}:SignedInfo>\n              <${ds}:SignatureValue></${ds}:SignatureValue>\n              <${ds}:KeyInfo Id="${key_id}">\n                 <${wsse}:SecurityTokenReference ${wsu}:Id="${sec_token_id}">\n                    <${wsse}:Reference URI="#${cert_id}" ValueType="${value_x509_url}"/>\n                 </${wsse}:SecurityTokenReference>\n              </${ds}:KeyInfo>\n            </${ds}:Signature>\n        </${wsse}:Security>\n        <${wsa_env}:Action>${action}</${wsa_env}:Action>\n        <${wsa_env}:To wsu:Id="${body_id}" xmlns:${wsu}="${wsu_url}">${to_url}</${wsa_env}:To>\n </${soap}:Header>\n <${soap}:Body></${soap}:Body>\n</${soap}:Envelope>')
namespaces_dict = {'soap': NS_SOAP, 
   'soap_url': NS_SOAP_URL, 
   'soap_env': NS_SOAP_ENV, 
   'soap_env_url': NS_SOAP_ENV_URL, 
   'wsse': NS_WSSE, 
   'wsse_url': NS_WSSE_URL, 
   'wsu': NS_WSU, 
   'wsu_url': NS_WSU_URL, 
   'wcf_env': NS_WCF, 
   'wcf_env_url': NS_WCF_URL, 
   'ds': NS_DS, 
   'ds_url': NS_DS_URL, 
   'ec': NS_EC, 
   'ec_url': NS_EC_URL, 
   'eet_url': NS_EET_URL, 
   'wsa_env': NS_WSA, 
   'wsa_env_url': NS_WSA_URL, 
   'eet_url': NS_EET_URL, 
   'algo_sha256': ALGORITHM_SHA256, 
   'algo_digest_sha256': ALGORITHM_DIGEST_SHA256, 
   'value_x509_url': VALUE_X509_URL, 
   'encoding_base64_url': ENCODING_BASE64_URL}

class SOAPSing(object):

    def __init__(self, signing, to_url='https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl'):
        """
        to_url: Default URL habilitacion
        """
        self.signing = signing
        self.to_url = to_url

    def get_normalized_subtree(self, node, includive_prefixes=[]):
        tree = etree.ElementTree(node)
        ss = StringIO()
        tree.write_c14n(ss, exclusive=True, inclusive_ns_prefixes=includive_prefixes)
        return ss.getvalue()

    def calculate_node_digest(self, node):
        data = self.get_normalized_subtree(node, ['soap', 'wcf', 'wsa', 'wsu'])
        return hashlib.sha256(data).digest()

    def sing(self, nodeSing, action):
        parser = etree.XMLParser(remove_blank_text=True, ns_clean=False)
        body_id = 'ID-' + uuid.uuid4().hex
        cert_id = 'X509-' + uuid.uuid4().hex
        sig_id = 'SIG-' + uuid.uuid4().hex
        key_id = 'KI-' + uuid.uuid4().hex
        sec_token_id = 'STR-' + uuid.uuid4().hex
        timestam_id = 'TS-' + uuid.uuid4().hex
        now = datetime.datetime.utcnow()
        nowExpire = now + datetime.timedelta(seconds=60000)
        values = dict(namespaces_dict)
        values.update({'body_id': body_id, 
           'timestam_id': timestam_id, 
           'cert_id': cert_id, 
           'sig_id': sig_id, 
           'key_id': key_id, 
           'timestamp_created': now.strftime('%Y-%m-%dT%H:%M:%SZ'), 
           'timestamp_expires': nowExpire.strftime('%Y-%m-%dT%H:%M:%SZ'), 
           'sec_token_id': sec_token_id, 
           'sec_token': base64.b64encode(self.signing.get_cert_binary()).decode('utf8'), 
           'action': action, 
           'to_url': self.to_url})
        envelope = etree.XML(envelope_template.substitute(values), parser=parser)
        body = find_node(envelope, 'Body', NS_SOAP_URL)
        body.append(nodeSing)
        to = find_node(envelope, 'To', NS_WSA_URL)
        body_digest = self.calculate_node_digest(to)
        digest_node = find_node(envelope, 'DigestValue', NS_DS_URL)
        digest_node.text = base64.b64encode(body_digest)
        signature_node = find_node(envelope, 'SignedInfo', NS_DS_URL)
        normalized_signing = self.get_normalized_subtree(signature_node, ['soap', 'wcf', 'wsa'])
        signature_value_node = find_node(envelope, 'SignatureValue', NS_DS_URL)
        signature_value_node.text = base64.b64encode(self.signing.sign_text(normalized_signing))
        return envelope