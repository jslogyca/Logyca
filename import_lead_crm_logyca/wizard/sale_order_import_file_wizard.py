# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import xlwt
import base64
import io
import xlsxwriter
import requests
import tempfile
import xlrd
import logging
import time
import re

import pytz


class SaleOrderImportFileWizard(models.TransientModel):
    _name = 'sale.order.import.file.wizard'
    _description = 'Purchase Order Import File Wizard'

    file_data = fields.Binary(string='File', required=True)
    filename = fields.Char(string='Name File')
    
    def validate_mail(self, email):
        if email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(email.lower()))
        if match == None:
            return False
        return True

    def import_file(self):
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno. \n\n Si no es posible cierre este asistente e intente de nuevo.')

        # valida que el archivo cargado se llame igual que la plantilla .xlsx
        try:
            tmp_file = tempfile.NamedTemporaryFile(delete = False)
            tmp_file.write(base64.b64decode(self and self.file_data or _('Invalid file')))
            tmp_file.close()
            xls_tmp_file = xlrd.open_workbook(tmp_file.name)
        except:
            raise ValidationError('No se puede leer el archivo. Verifique que el formato sea el correcto.')
            return False

        sheet = xls_tmp_file.sheet_by_name(xls_tmp_file.sheet_names()[0])
        record_list = [sheet.row_values(i) for i in range(sheet.nrows)]
        record_list = record_list[1:]
        #contador de registros en el excel
        count=1
        #contador de postulaciones creadas correctamente en odoo.
        cre=[]
        #almacena las excepciones
        errors=[]
        #almacena las excepciones
        error=[]

        partner_id = None
        company_id = None
        for fila in record_list:
            if fila[1]:
                partner_nit = str(fila[3])
                company_name = str(fila[0])
                description = str(fila[2])
                suffix = ".0"
                if partner_nit.endswith(suffix):
                    partner_nit = partner_nit[:-len(suffix)]
                partner_id = self.env['res.partner'].search([('vat','=',str(partner_nit)), ('parent_id','=',None)], limit=1)
                company_id = self.env['res.company'].search([('name','=',str(company_name))], limit=1)

                sale_order_values = {
                    'partner_id' : partner_id.id,
                    'company_id' : company_id.id,
                    'partner_ref': str(description),
                    # 'validity_date' : self.invoicing_companies.expiration_date
                }

                sale_order = self.env['purchase.order'].create(sale_order_values)
                break

        sale_order_line_values = []
        for fila in record_list:
            count+=1

            #validar si están los NIT de las empresas (benef y halonadora)
            if fila[1]:
                description = str(fila[2])
                budget_name = str(fila[5])
                analytic_name = str(fila[6])
                consumo = fila[7]
                descuento = fila[8]
                total = fila[9]
                iva = fila[10]
                budget_group_id = self.env['logyca.budget_group'].search([('name','=',str(budget_name)), ('company_id','=',company_id.id)], limit=1)
                if analytic_name:
                    analytic_id = self.env['account.analytic.account'].search([('name','=',str(analytic_name)), ('company_id','=',company_id.id)], limit=1)

                if consumo and consumo>0.0:
                    if not budget_group_id.by_default_group:
                        product_id = self.env['product.product'].search([('id','=',1238)], order="id asc", limit=1)
                        if not product_id:
                            product_id = self.env['product.product'].search([('id','=',36)], order="id asc", limit=1)
                    else:
                        product_id = self.env['product.product'].search([('id','=',1185)], order="id asc", limit=1)
                        if not product_id:
                            product_id = self.env['product.product'].search([('id','=',16)], order="id asc", limit=1)
                    vals ={
                        'order_id' : sale_order.id,
                        'product_id' : product_id.id,
                        'product_uom_qty' : 1,
                        'price_unit' : consumo,
                        'x_budget_group': budget_group_id.id,
                        'analytic_distribution': budget_group_id.analytic_distribution,
                        'company_id' : company_id.id,
                    }
                    sale_order_line_values.append((0, 0, vals))

                if total and total>0.0:
                    if not budget_group_id.by_default_group:
                        product_id = self.env['product.product'].search([('id','=',1260)], order="id asc", limit=1)
                        if not product_id:
                            product_id = self.env['product.product'].search([('id','=',17)], order="id asc", limit=1)
                    else:
                        product_id = self.env['product.product'].search([('id','=',1201)], order="id asc", limit=1)
                        if not product_id:
                            product_id = self.env['product.product'].search([('id','=',18)], order="id asc", limit=1)
                    taxes = product_id.supplier_taxes_id.filtered(lambda t: t.company_id == company_id)
                    if iva and iva > 0.0:
                        vals = {
                            'order_id': sale_order.id,
                            'product_id': product_id.id,
                            'product_uom_qty': 1,
                            'price_unit': total,
                            'x_budget_group': budget_group_id.id,
                            'analytic_distribution': budget_group_id.analytic_distribution,
                            'company_id' : company_id.id,
                            'taxes_id' : [(6, 0, taxes.ids)],
                        }
                    else:
                        vals = {
                            'order_id'         : sale_order.id,
                            'product_id'       : product_id.id,
                            'product_uom_qty'  : 1,
                            'price_unit'       : total,  # Odoo se encarga si el impuesto es price_include
                            'x_budget_group'   : budget_group_id.id,
                            'analytic_distribution': budget_group_id.analytic_distribution,
                            'company_id'       : company_id.id,
                        }
                    sale_order_line_values.append((0, 0, vals))

                if descuento and descuento>0.0:
                    product_id = self.env['product.product'].search([('id','=',1355)], order="id asc", limit=1)
                    if not product_id:
                        product_id = self.env['product.product'].search([('id','=',19)], order="id asc", limit=1)

                    vals = {
                        'order_id': sale_order.id,
                        'product_id': product_id.id,
                        'product_uom_qty': 1,
                        'price_unit': descuento,
                        'x_budget_group': budget_group_id.id,
                        'analytic_distribution': budget_group_id.analytic_distribution,
                    }
                    sale_order_line_values.append((0, 0, vals))

                try:
                    with self._cr.savepoint():
                        # sale_order_line = self.env['purchase.order.line'].create(sale_order_line_values)
                        sale_order.write({'order_line': sale_order_line_values})
                except Exception as e:
                    validation = "Fila %s: %s no se pudo crear como empresa beneficiaria. %s" % (str(count), partner_id.vat + '-' + str(partner_id.name.strip()),str(e))
                    errors.append(validation)
                    continue
                cre.append(sale_order.id)
                self.env.cr.commit()

        if len(errors)>=1:
            error.append(errors)
        if error:
            msj='El resultado de la importación es: \n\n'
            for e in errors:
                msj+=str(e)
                msj+='\n\n'

            raise ValidationError(msj)
        view_id = self.env.ref('purchase.purchase_order_form').id,

        if not cre:
            raise UserError(_("No se importaron los beneficios"))

        if isinstance(cre, int):
            res_id = cre
        elif hasattr(cre, 'ids'):        # recordset
            res_id = cre.ids[0]          # o cre.ids[-1] si prefieres el último
        else:
            res_id = cre[0]

        return {
            'name': _('Registros Importados %s') % fields.Date.today().strftime("%d/%m/%Y"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': res_id,            # <- clave para abrir el registro
            'target': 'current',
        }        
