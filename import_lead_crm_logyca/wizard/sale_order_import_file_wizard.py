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
    validation_result = fields.Text(string='Resultado de Validación', readonly=True)
    
    def validate_mail(self, email):
        if email:
            match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', str(email.lower()))
        if match == None:
            return False
        return True

    def action_validate_data(self):
        """
        Botón de validación que verifica:
        1. Si el grupo presupuestal existe
        2. Si la cuenta analítica existe
        3. Si el proveedor existe
        4. Si existe una orden de compra con la misma referencia
        """
        if not self.file_data:
            raise ValidationError('No se encuentra un archivo, por favor cargue uno.')

        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_file.write(base64.b64decode(self.file_data or _('Invalid file')))
            tmp_file.close()
            xls_tmp_file = xlrd.open_workbook(tmp_file.name)
        except:
            raise ValidationError('No se puede leer el archivo. Verifique que el formato sea el correcto.')

        sheet = xls_tmp_file.sheet_by_name(xls_tmp_file.sheet_names()[0])
        record_list = [sheet.row_values(i) for i in range(sheet.nrows)]
        record_list = record_list[1:]  # Saltar encabezados

        errors = []
        warnings = []
        row_num = 1

        # Variables para validar referencia única
        partner_nit = None
        company_name = None
        reference = None

        for fila in record_list:
            row_num += 1
            if not fila[1]:  # Si no hay datos relevantes
                continue

            # Extraer datos de la fila
            company_name_row = str(fila[0]) if fila[0] else ''
            partner_nit_row = str(fila[3]) if fila[3] else ''
            reference_row = str(fila[2]) if fila[2] else ''
            description = str(fila[4]) if len(fila) > 4 and fila[4] else ''  # NUEVA COLUMNA
            budget_name = str(fila[5]) if len(fila) > 5 and fila[5] else ''
            analytic_name = str(fila[6]) if len(fila) > 6 and fila[6] else ''

            # Limpiar NIT
            suffix = ".0"
            if partner_nit_row.endswith(suffix):
                partner_nit_row = partner_nit_row[:-len(suffix)]

            # Guardar datos de la primera fila para validación de referencia
            if row_num == 2:
                partner_nit = partner_nit_row
                company_name = company_name_row
                reference = reference_row

            # VALIDACIÓN 1: Verificar que el proveedor existe
            if partner_nit_row:
                partner_id = self.env['res.partner'].search([
                    ('vat', '=', partner_nit_row),
                    ('parent_id', '=', False)
                ], limit=1)
                
                if not partner_id:
                    errors.append(f"Fila {row_num}: Proveedor con NIT '{partner_nit_row}' no existe en el sistema")

            # Verificar compañía
            if company_name_row:
                company_id = self.env['res.company'].search([
                    ('name', '=', company_name_row)
                ], limit=1)
                
                if not company_id:
                    errors.append(f"Fila {row_num}: Compañía '{company_name_row}' no existe en el sistema")
            else:
                company_id = self.env.company

            # VALIDACIÓN 2: Verificar que el grupo presupuestal existe
            if budget_name:
                budget_group_id = self.env['logyca.budget_group'].search([
                    ('name', '=', budget_name),
                    ('company_id', '=', company_id.id if company_id else self.env.company.id)
                ], limit=1)
                
                if not budget_group_id:
                    errors.append(f"Fila {row_num}: Grupo Presupuestal '{budget_name}' no existe para la compañía {company_name_row}")

            # VALIDACIÓN 3: Verificar que la cuenta analítica existe
            if analytic_name:
                analytic_id = self.env['account.analytic.account'].search([
                    ('name', '=', analytic_name.strip()),
                    '|',
                    ('company_id', '=', company_id.id if company_id else self.env.company.id),
                    ('company_id', '=', False)
                ], limit=1)
                
                if not analytic_id:
                    errors.append(f"Fila {row_num}: Cuenta Analítica '{analytic_name}' no existe")

        # VALIDACIÓN 4: Verificar si existe una orden de compra con la misma referencia
        if reference and partner_nit and company_name:
            partner_id = self.env['res.partner'].search([
                ('vat', '=', partner_nit),
                ('parent_id', '=', False)
            ], limit=1)
            
            company_id = self.env['res.company'].search([
                ('name', '=', company_name)
            ], limit=1)

            if partner_id and company_id:
                existing_po = self.env['purchase.order'].search([
                    ('partner_ref', '=', reference),
                    ('partner_id', '=', partner_id.id),
                    ('company_id', '=', company_id.id)
                ], limit=1)
                
                if existing_po:
                    errors.append(f"CRÍTICO: Ya existe una Orden de Compra con la referencia '{reference}' para el proveedor {partner_id.name} (ID: {existing_po.name})")

        # Construir mensaje de resultado
        result_message = "=== RESULTADO DE LA VALIDACIÓN ===\n\n"
        
        if not errors and not warnings:
            result_message += "✓ VALIDACIÓN EXITOSA\n\n"
            result_message += "Todos los datos son correctos. Puede proceder con la importación.\n\n"
            result_message += f"- Registros a procesar: {len([f for f in record_list if f[1]])}\n"
            result_message += f"- Proveedor: {partner_nit}\n"
            result_message += f"- Referencia: {reference}\n"
        else:
            result_message += "✗ SE ENCONTRARON ERRORES\n\n"
            result_message += f"Total de errores: {len(errors)}\n"
            result_message += f"Total de advertencias: {len(warnings)}\n\n"
            
            if errors:
                result_message += "ERRORES:\n"
                for error in errors:
                    result_message += f"  • {error}\n"
                result_message += "\n"
            
            if warnings:
                result_message += "ADVERTENCIAS:\n"
                for warning in warnings:
                    result_message += f"  • {warning}\n"
                result_message += "\n"
            
            result_message += "Por favor corrija estos problemas antes de importar.\n"

        # Actualizar el campo de resultado
        self.validation_result = result_message

        # Mostrar mensaje en pantalla
        if errors:
            raise ValidationError(result_message)
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validación Exitosa',
                    'message': 'Todos los datos son correctos. Puede proceder con la importación.',
                    'type': 'success',
                    'sticky': False,
                }
            }

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
                }

                sale_order = self.env['purchase.order'].create(sale_order_values)
                break

        sale_order_line_values = []
        for fila in record_list:
            sale_order_line_values = []
            count+=1

            #validar si están los NIT de las empresas (benef y halonadora)
            if fila[1]:
                description = str(fila[2])
                line_description = str(fila[4]) if len(fila) > 4 and fila[4] else ''  # NUEVA COLUMNA DESCRIPCIÓN
                budget_name = str(fila[5]) if len(fila) > 5 else ''
                analytic_name = str(fila[6]) if len(fila) > 6 else ''
                consumo = fila[7] if len(fila) > 7 else 0.0
                descuento = fila[8] if len(fila) > 8 else 0.0
                total = fila[9] if len(fila) > 9 else 0.0
                iva = fila[10] if len(fila) > 10 else 0.0
                
                budget_group_id = self.env['logyca.budget_group'].search([('name','=',str(budget_name)), ('company_id','=',company_id.id)], limit=1)
                if analytic_name:
                    analytic_id = self.env['account.analytic.account'].search([('name', '=', (str(analytic_name)).strip()), '|', 
                                    ('company_id', '=', company_id.id), ('company_id', '=', False),], limit=1)

                if consumo and consumo>0.0:
                    if not budget_group_id.by_default_group:
                        if budget_group_id and (budget_group_id.name or '').strip().upper().startswith('AD'):
                            product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                    ('company_id','=',company_id.id),
                                                    ('product_type','=','ga'),
                                                    ('amount_type','=','consumo')], order="id asc", limit=1)
                            vals = {
                                'order_id': sale_order.id,
                                'product_id': product_id.product_id.id,
                                'name': line_description or product_id.product_id.display_name,
                                'product_qty': 1,
                                'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                'price_unit': consumo,
                                'x_budget_group': budget_group_id.id,
                                'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                'company_id': company_id.id,
                            }
                            sale_order_line_values.append((0, 0, vals))
                        else:
                            product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                    ('company_id','=',company_id.id),
                                                    ('product_type','=','gv'),
                                                    ('amount_type','=','consumo')], order="id asc", limit=1)
                            vals = {
                                'order_id': sale_order.id,
                                'product_id': product_id.product_id.id,
                                'name': line_description or product_id.product_id.display_name,
                                'product_qty': 1,
                                'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                'price_unit': consumo,
                                'x_budget_group': budget_group_id.id,
                                'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                'company_id': company_id.id,
                            }
                            sale_order_line_values.append((0, 0, vals))                            
                    else:
                        product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                ('company_id','=',company_id.id),
                                                ('product_type','=','co'),
                                                ('amount_type','=','consumo')], order="id asc", limit=1)
                        vals = {
                            'order_id': sale_order.id,
                            'product_id': product_id.product_id.id,
                            'name': line_description or product_id.product_id.display_name,
                            'product_qty': 1,
                            'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                            'price_unit': consumo,
                            'x_budget_group': budget_group_id.id,
                            'analytic_distribution': {analytic_id.id: 100.0} if analytic_id else {},
                            'company_id': company_id.id,
                        }
                        sale_order_line_values.append((0, 0, vals))

                if total and total>0.0:
                    if not budget_group_id.by_default_group:
                        if budget_group_id and (budget_group_id.name or '').strip().upper().startswith('AD'):
                            product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                    ('company_id','=',company_id.id),
                                                    ('product_type','=','ga'),
                                                    ('amount_type','=','total')], order="id asc", limit=1)
                            taxes = product_id.product_id.supplier_taxes_id.filtered(lambda t: t.company_id == company_id)
                            if iva and iva > 0.0:
                                vals = {
                                    'order_id': sale_order.id,
                                    'product_id': product_id.product_id.id,
                                    'name': line_description or product_id.product_id.display_name,
                                    'product_qty': 1,
                                    'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                    'price_unit': total,
                                    'x_budget_group': budget_group_id.id,
                                    'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                    'company_id': company_id.id,
                                    'taxes_id': [(6, 0, taxes.ids)],
                                }
                            else:
                                vals = {
                                    'order_id': sale_order.id,
                                    'product_id': product_id.product_id.id,
                                    'name': line_description or product_id.product_id.display_name,
                                    'product_qty': 1,
                                    'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                    'price_unit': total,
                                    'x_budget_group': budget_group_id.id,
                                    'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                    'company_id': company_id.id,
                                }
                            sale_order_line_values.append((0, 0, vals))
                        else:
                            product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                    ('company_id','=',company_id.id),
                                                    ('product_type','=','gv'),
                                                    ('amount_type','=','total')], order="id asc", limit=1)
                            taxes = product_id.product_id.supplier_taxes_id.filtered(lambda t: t.company_id == company_id)
                            if iva and iva > 0.0:
                                vals = {
                                    'order_id': sale_order.id,
                                    'product_id': product_id.product_id.id,
                                    'name': line_description or product_id.product_id.display_name,
                                    'product_qty': 1,
                                    'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                    'price_unit': total,
                                    'x_budget_group': budget_group_id.id,
                                    'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                    'company_id': company_id.id,
                                    'taxes_id': [(6, 0, taxes.ids)],
                                }
                            else:
                                vals = {
                                    'order_id': sale_order.id,
                                    'product_id': product_id.product_id.id,
                                    'name': line_description or product_id.product_id.display_name,
                                    'product_qty': 1,
                                    'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                    'price_unit': total,
                                    'x_budget_group': budget_group_id.id,
                                    'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                                    'company_id': company_id.id,
                                }
                            sale_order_line_values.append((0, 0, vals))                                                        

                    else:
                        product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                                ('company_id','=',company_id.id),
                                                ('product_type','=','co'),
                                                ('amount_type','=','total')], order="id asc", limit=1)
                        taxes = product_id.product_id.supplier_taxes_id.filtered(lambda t: t.company_id == company_id)
                        if iva and iva > 0.0:
                            vals = {
                                'order_id': sale_order.id,
                                'product_id': product_id.product_id.id,
                                'name': line_description or product_id.product_id.display_name,
                                'product_qty': 1,
                                'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                'price_unit': total,
                                'x_budget_group': budget_group_id.id,
                                'analytic_distribution': {analytic_id.id: 100.0} if analytic_id else {},
                                'company_id': company_id.id,
                                'taxes_id': [(6, 0, taxes.ids)],
                            }
                        else:
                            vals = {
                                'order_id': sale_order.id,
                                'product_id': product_id.product_id.id,
                                'name': line_description or product_id.product_id.display_name,
                                'product_qty': 1,
                                'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                                'price_unit': total,
                                'x_budget_group': budget_group_id.id,
                                'analytic_distribution': {analytic_id.id: 100.0} if analytic_id else {},
                                'company_id': company_id.id,
                            }
                        sale_order_line_values.append((0, 0, vals))

                if descuento and descuento>0.0:
                    product_id = self.env['partner.product.purchase'].search([('partner_id','=',partner_id.id), 
                                            ('company_id','=',company_id.id),
                                            ('product_type','=','na')], order="id asc", limit=1)
                    vals = {
                        'order_id': sale_order.id,
                        'product_id': product_id.product_id.id,
                        'name': line_description or product_id.product_id.display_name,
                        'product_qty': 1,
                        'product_uom': product_id.product_id.uom_po_id.id or product_id.product_id.uom_id.id,
                        'price_unit': descuento,
                        'x_budget_group': budget_group_id.id,
                        'analytic_distribution': budget_group_id.analytic_distribution if budget_group_id.analytic_distribution else {},
                    }
                    sale_order_line_values.append((0, 0, vals))

                try:
                    with self._cr.savepoint():
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
        elif hasattr(cre, 'ids'):
            res_id = cre.ids[0]
        else:
            res_id = cre[0]

        return {
            'name': _('Registros Importados %s') % fields.Date.today().strftime("%d/%m/%Y"),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'res_id': res_id,
            'target': 'current',
        }
