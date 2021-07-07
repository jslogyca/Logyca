# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class EpayrollImportFileWizard(models.TransientModel):
    _name = 'epayroll.import.file.wizard'
    _description = 'Cargue Masivo Nominas de Heinshon'


    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    payslip_batch_id = fields.Many2one('hr.payslip.run', string='payslip batch')
    company_id = fields.Many2one('res.company', string='Company')                        
        

    def import_file(self):
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno. \n\n Si no es posible cierre este asistente e intente de nuevo.')

        return True
