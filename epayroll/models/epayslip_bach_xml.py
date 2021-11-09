# -*- coding: utf-8 -*-

SendNominaSync = {'action': 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendNominaSync', 
   'body': '\n            <wcf:SendNominaSync>\n                <!--Optional:-->\n                <wcf:fileName>%(zip_fileName)s</wcf:fileName>\n                <!--Optional:-->\n                <wcf:contentFile>%(zip_data)s</wcf:contentFile>\n            </wcf:SendNominaSync>\n        ', 
   'DianResponse': '{http://schemas.datacontract.org/2004/07/DianResponse}DianResponse', 
   'ErrorMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}ErrorMessage', 
   'string': '{http://schemas.microsoft.com/2003/10/Serialization/Arrays}string', 
   'IsValid': '{http://schemas.datacontract.org/2004/07/DianResponse}IsValid', 
   'StatusCode': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusCode', 
   'StatusDescription': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusDescription', 
   'StatusMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusMessage', 
   'XmlDocumentKey': '{http://schemas.datacontract.org/2004/07/DianResponse}XmlDocumentKey', 
   'XmlBase64Bytes': '{http://schemas.datacontract.org/2004/07/DianResponse}XmlBase64Bytes', 
   'IssueTime': '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime', 
   'IssueDate': '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate', 
   'LineResponse': '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LineResponse'}

SendTestSetAsync = {'action': 'http://wcf.dian.colombia/IWcfDianCustomerServices/SendTestSetAsync',
   'body': '\n            <wcf:SendTestSetAsync>\n                <!--Optional:-->\n                <wcf:fileName>%(zip_fileName)s</wcf:fileName>\n                <!--Optional:-->\n                <wcf:contentFile>%(zip_data)s</wcf:contentFile>\n                <!--Optional:-->\n                <wcf:testSetId>%(TestSetId)s</wcf:testSetId>\n            </wcf:SendTestSetAsync>\n        ', 
   'ZipKey': '{http://schemas.datacontract.org/2004/07/UploadDocumentResponse}ZipKey', 
   'ErrorMessageList': '{http://schemas.datacontract.org/2004/07/UploadDocumentResponse}ErrorMessageList'}

GetStatusZip = {'action': 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatusZip', 
   'body': '\n            <wcf:GetStatusZip>\n                <!--Optional:-->\n                <wcf:trackId>%(trackId)s</wcf:trackId>\n            </wcf:GetStatusZip>\n        ', 
   'DianResponse': '{http://schemas.datacontract.org/2004/07/DianResponse}DianResponse', 
   'ErrorMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}ErrorMessage', 
   'string': '{http://schemas.microsoft.com/2003/10/Serialization/Arrays}string', 
   'IsValid': '{http://schemas.datacontract.org/2004/07/DianResponse}IsValid', 
   'StatusCode': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusCode', 
   'StatusDescription': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusDescription', 
   'StatusMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusMessage'}

GetStatus = {'action': 'http://wcf.dian.colombia/IWcfDianCustomerServices/GetStatus', 
   'body': '\n            <wcf:GetStatus>\n                <!--Optional:-->\n                <wcf:trackId>%(trackId)s</wcf:trackId>\n            </wcf:GetStatus>\n        ', 
   'DianResponse': '{http://schemas.datacontract.org/2004/07/DianResponse}DianResponse', 
   'ErrorMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}ErrorMessage', 
   'string': '{http://schemas.microsoft.com/2003/10/Serialization/Arrays}string', 
   'IsValid': '{http://schemas.datacontract.org/2004/07/DianResponse}IsValid', 
   'StatusCode': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusCode', 
   'StatusDescription': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusDescription', 
   'StatusMessage': '{http://schemas.datacontract.org/2004/07/DianResponse}StatusMessage', 
   'XmlDocumentKey': '{http://schemas.datacontract.org/2004/07/DianResponse}XmlDocumentKey', 
   'XmlBase64Bytes': '{http://schemas.datacontract.org/2004/07/DianResponse}XmlBase64Bytes', 
   'IssueTime': '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueTime', 
   'IssueDate': '{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate', 
   'LineResponse': '{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}LineResponse'}   