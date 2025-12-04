# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import xlrd
import base64
import tempfile
import re


class HrExpenseImportWizard(models.TransientModel):
    _name = 'hr.expense.import.wizard'
    _description = 'HR Expense Import Wizard'

    file_data = fields.Binary(string='Archivo Excel', required=True)
    filename = fields.Char(string='Nombre del Archivo')
    validation_result = fields.Text(string='Resultado de Validación', readonly=True)
    payment_mode = fields.Selection([
        ('own_account', 'Cuenta Propia del Empleado'),
        ('company_account', 'Cuenta de la Compañía'),
        ('credit_card', 'Tarjeta de Crédito')
    ], string='Pagador por', required=True, default='company_account')
    credit_card_id = fields.Many2one(
        'credit.card',
        string='Tarjeta de Crédito',
        help='Tarjeta de crédito asociada al reporte de gastos'
    )
    agrupar_por_factura = fields.Boolean(
        string='Agrupar por Factura',
        default=False,
        help='Si está activado, al contabilizar el gasto se generará una sola CXP al tercero '
             'de la tarjeta de crédito. Si está desactivado, se generará una CXP por cada gasto.'
    )
    documento_soporte = fields.Boolean(
        string='Documento Soporte',
        default=False,
        help='Si está activado, al contabilizar se generará la CXP a cada proveedor de las líneas de gasto '
             'en lugar de al banco o tarjeta de crédito. Se utilizará el diario configurado como documento soporte.'
    )

    @api.onchange('payment_mode')
    def _onchange_payment_mode(self):
        """Limpiar tarjeta de crédito si no es necesaria"""
        if self.payment_mode != 'credit_card':
            self.credit_card_id = False

    def action_validate_data(self):
        """
        Validar los datos del archivo Excel antes de importar:
        1. Validar que el proveedor existe
        2. Validar que el empleado existe
        3. Validar que el grupo presupuestal o cuenta analítica existe (Columna I)
        4. Validar que existe configuración de producto para el proveedor
        5. Validar que no exista ya un reporte con la misma referencia
        
        NUEVA FUNCIONALIDAD 3: Incluir fecha de contabilización (columna adicional)
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

        # Diccionario para agrupar por referencia
        references_dict = {}

        for fila in record_list:
            row_num += 1
            if not fila or not any(fila):  # Si la fila está vacía
                continue

            # Extraer datos de la fila según el template
            company_name = str(fila[0]) if fila[0] else ''
            date_value = fila[1] if len(fila) > 1 else ''
            reference = str(fila[2]) if len(fila) > 2 and fila[2] else ''
            partner_vat = str(fila[3]) if len(fila) > 3 and fila[3] else ''
            description = str(fila[4]) if len(fila) > 4 and fila[4] else ''
            tax_excluded_desc = str(fila[5]) if len(fila) > 5 and fila[5] else ''
            partner_name = str(fila[6]) if len(fila) > 6 and fila[6] else ''
            employee_name = str(fila[7]) if len(fila) > 7 and fila[7] else ''
            budget_or_analytic_name = str(fila[8]) if len(fila) > 8 and fila[8] else ''
            total_amount = float(fila[9]) if len(fila) > 9 and fila[9] else 0.0
            tax_excluded = float(fila[10]) if len(fila) > 10 and fila[10] else 0.0
            tax_amount = float(fila[11]) if len(fila) > 11 and fila[11] else 0.0
            # NUEVA FUNCIONALIDAD 3: Leer fecha de contabilización (columna 12 - índice 12)
            accounting_date_value = fila[12] if len(fila) > 12 else ''

            # Limpiar NIT (remover .0 si existe)
            suffix = ".0"
            if partner_vat.endswith(suffix):
                partner_vat = partner_vat[:-len(suffix)]
            if employee_name.endswith(suffix):
                employee_name = employee_name[:-len(suffix)]

            # Guardar referencia para validación posterior
            if reference:
                if reference not in references_dict:
                    references_dict[reference] = {
                        'company_name': company_name,
                        'employee_name': employee_name,
                        'count': 0,
                        'accounting_date': accounting_date_value  # Guardar fecha de contabilización
                    }
                references_dict[reference]['count'] += 1

            # VALIDACIÓN 1: Verificar que la compañía existe
            company_id = None
            if company_name:
                company_id = self.env['res.company'].search([
                    ('name', '=', company_name)
                ], limit=1)
                if not company_id:
                    errors.append(f"Fila {row_num}: Compañía '{company_name}' no existe en el sistema")
            else:
                company_id = self.env.company

            # VALIDACIÓN 2: Verificar que el proveedor existe
            partner_id = None
            if partner_vat:
                partner_id = self.env['res.partner'].search([
                    ('vat', '=', partner_vat),
                    ('parent_id', '=', False)
                ], limit=1)
                if not partner_id:
                    errors.append(f"Fila {row_num}: Proveedor con NIT '{partner_vat}' no existe en el sistema")
                else:
                    # VALIDACIÓN 3: Verificar que existe configuración de producto para el proveedor
                    if company_id:
                        product_config = self.env['partner.product.purchase'].search([
                            ('partner_id', '=', partner_id.id),
                            ('company_id', '=', company_id.id)
                        ], limit=1)
                        print('//////', product_config, partner_id.name)
                        if not product_config:
                            print('////// 2222', product_config, partner_id.name)
                            warnings.append(
                                f"Fila {row_num}: No existe configuración de productos para el proveedor "
                                f"'{partner_id.name}' en la compañía '{company_id.name}'"
                            )

            # VALIDACIÓN 4: Verificar que el empleado existe
            employee_id = None
            if employee_name:
                employee_id = self.env['hr.employee'].search([
                    ('identification_id', '=', employee_name)
                ], limit=1)
                if not employee_id:
                    errors.append(f"Fila {row_num}: Empleado '{employee_name}' no existe en el sistema")

            # VALIDACIÓN 5: Verificar que el grupo presupuestal o cuenta analítica existe (Columna I)
            budget_group = None
            analytic_account = None
            if budget_or_analytic_name and company_id:
                # Primero intentar buscar como grupo presupuestal
                budget_group = self.env['logyca.budget_group'].search([
                    ('name', '=', budget_or_analytic_name),
                    ('company_id', '=', company_id.id)
                ], limit=1)
                
                # Si no es grupo presupuestal, buscar como cuenta analítica
                if not budget_group:
                    analytic_account = self.env['account.analytic.account'].search([
                        ('name', '=', budget_or_analytic_name.strip()),
                        ('company_id', '=', company_id.id)
                    ], limit=1)
                    
                    if not analytic_account:
                        errors.append(
                            f"Fila {row_num}: No se encontró grupo presupuestal ni cuenta analítica "
                            f"con el nombre '{budget_or_analytic_name}' en la compañía '{company_id.name}'"
                        )

        # VALIDACIÓN 6: Verificar que no existan reportes con las mismas referencias
        existing_references = []
        for reference in references_dict.keys():
            existing_sheet = self.env['hr.expense.sheet'].search([
                ('name', '=', reference)
            ], limit=1)
            if existing_sheet:
                existing_references.append(reference)

        if existing_references:
            errors.append(
                f"Las siguientes referencias ya existen en el sistema: {', '.join(existing_references)}"
            )

        # Mostrar resultado de validación
        result_text = ""
        if errors:
            result_text += "=== ERRORES ===\n\n"
            result_text += '\n'.join(errors)
            result_text += "\n\n"
        
        if warnings:
            result_text += "=== ADVERTENCIAS ===\n\n"
            result_text += '\n'.join(warnings)
            result_text += "\n\n"
        
        if not errors:
            result_text += f"=== RESUMEN ===\n\n"
            result_text += f"Total de reportes a importar: {len(references_dict)}\n"
            for ref, data in references_dict.items():
                result_text += f"  - {ref}: {data['count']} gastos\n"
            result_text += "\n✓ Validación exitosa. Puede proceder con la importación."
        else:
            result_text += "✗ Se encontraron errores. Por favor corrija el archivo antes de importar."

        self.validation_result = result_text
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_import_expenses(self):
        """
        Importar los gastos desde el archivo Excel
        
        NUEVA FUNCIONALIDAD 3: Guardar accounting_date de la columna 12
        NUEVA FUNCIONALIDAD 4: Dejar los gastos en estado aprobado
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
        row_num = 1
        expenses_by_reference = {}
        created_sheets = []

        for fila in record_list:
            row_num += 1
            if not fila or not any(fila):
                continue

            try:
                # Extraer datos
                company_name = str(fila[0]) if fila[0] else ''
                date_value = fila[1] if len(fila) > 1 else ''
                reference = str(fila[2]) if len(fila) > 2 and fila[2] else ''
                partner_vat = str(fila[3]) if len(fila) > 3 and fila[3] else ''
                description = str(fila[4]) if len(fila) > 4 and fila[4] else ''
                tax_excluded_desc = str(fila[5]) if len(fila) > 5 and fila[5] else ''
                partner_name = str(fila[6]) if len(fila) > 6 and fila[6] else ''
                employee_name = str(fila[7]) if len(fila) > 7 and fila[7] else ''
                budget_or_analytic_name = str(fila[8]) if len(fila) > 8 and fila[8] else ''
                total_amount = float(fila[9]) if len(fila) > 9 and fila[9] else 0.0
                tax_excluded = float(fila[10]) if len(fila) > 10 and fila[10] else 0.0
                tax_amount = float(fila[11]) if len(fila) > 11 and fila[11] else 0.0
                # NUEVA FUNCIONALIDAD 3: Leer fecha de contabilización
                accounting_date_value = fila[12] if len(fila) > 12 else ''

                # Limpiar NIT
                suffix = ".0"
                if partner_vat.endswith(suffix):
                    partner_vat = partner_vat[:-len(suffix)]
                if employee_name.endswith(suffix):
                    employee_name = employee_name[:-len(suffix)]

                # Buscar compañía
                company_id = self.env.company
                if company_name:
                    company_id = self.env['res.company'].search([
                        ('name', '=', company_name)
                    ], limit=1)
                    if not company_id:
                        errors.append(f"Fila {row_num}: Compañía '{company_name}' no encontrada")
                        continue

                # Buscar proveedor
                partner_id = self.env['res.partner'].search([
                    ('vat', '=', partner_vat),
                    ('parent_id', '=', False)
                ], limit=1)
                if not partner_id:
                    errors.append(f"Fila {row_num}: Proveedor con NIT '{partner_vat}' no encontrado")
                    continue

                # Buscar empleado
                employee_id = self.env['hr.employee'].search([
                    ('identification_id', '=', employee_name)
                ], limit=1)
                if not employee_id:
                    errors.append(f"Fila {row_num}: Empleado '{employee_name}' no encontrado")
                    continue

                # Buscar grupo presupuestal o cuenta analítica
                budget_group_id = self.env['logyca.budget_group'].search([
                    ('name', '=', budget_or_analytic_name),
                    ('company_id', '=', company_id.id)
                ], limit=1)
                
                analytic_id = None
                if not budget_group_id:
                    analytic_id = self.env['account.analytic.account'].search([
                        ('name', '=', budget_or_analytic_name.strip()),
                        ('company_id', '=', company_id.id)
                    ], limit=1)
                    
                    if not analytic_id:
                        errors.append(
                            f"Fila {row_num}: No se encontró grupo presupuestal ni cuenta analítica "
                            f"'{budget_or_analytic_name}'"
                        )
                        continue

                # Buscar producto
                product_id = None
                if budget_group_id:
                    if not budget_group_id.by_default_group:
                        # Determinar tipo de producto según el grupo presupuestal
                        if (budget_group_id.name or '').strip().upper().startswith('AD'):
                            # Tipo GA (Gasto Administrativo)
                            product_config = self.env['partner.product.purchase'].search([
                                ('partner_id', '=', partner_id.id),
                                ('company_id', '=', company_id.id),
                                ('product_type', '=', 'ga'),
                                ('amount_type', '=', 'total')
                            ], order="id asc", limit=1)
                        else:
                            # Tipo GV (Gasto de Venta)
                            product_config = self.env['partner.product.purchase'].search([
                                ('partner_id', '=', partner_id.id),
                                ('company_id', '=', company_id.id),
                                ('product_type', '=', 'gv'),
                                ('amount_type', '=', 'total')
                            ], order="id asc", limit=1)
                    else:
                        # Tipo CO (Costo)
                        product_config = self.env['partner.product.purchase'].search([
                            ('partner_id', '=', partner_id.id),
                            ('company_id', '=', company_id.id),
                            ('product_type', '=', 'co'),
                            ('amount_type', '=', 'total')
                        ], order="id asc", limit=1)
                    
                    if product_config:
                        product_id = product_config.product_id
                else:
                    product_config = self.env['partner.product.purchase'].search([
                        ('partner_id', '=', partner_id.id),
                        ('company_id', '=', company_id.id),
                        ('product_type', '=', 'co'),
                        ('amount_type', '=', 'total')
                    ], order="id asc", limit=1)
                    if product_config:
                        product_id = product_config.product_id
                        
                if not product_id:
                    errors.append(
                        f"Fila {row_num}: No se encontró configuración de producto para el proveedor "
                        f"'{partner_id.name}' en la compañía '{company_id.name}'"
                    )
                    continue

                # Convertir fecha de gasto
                expense_date = datetime.today().date()
                if date_value:
                    try:
                        if isinstance(date_value, float):
                            expense_date = xlrd.xldate_as_datetime(date_value, xls_tmp_file.datemode).date()
                        else:
                            expense_date = datetime.strptime(str(date_value), '%Y-%m-%d').date()
                    except:
                        pass

                # NUEVA FUNCIONALIDAD 3: Convertir fecha de contabilización
                accounting_date = None
                if accounting_date_value:
                    try:
                        if isinstance(accounting_date_value, float):
                            accounting_date = xlrd.xldate_as_datetime(accounting_date_value, xls_tmp_file.datemode).date()
                        else:
                            accounting_date = datetime.strptime(str(accounting_date_value), '%Y-%m-%d').date()
                    except:
                        pass  # Si no se puede convertir, dejar como None

                # Preparar distribución analítica
                analytic_distribution = {}
                if analytic_id:
                    analytic_distribution = {analytic_id.id: 100.0}
                elif budget_group_id and budget_group_id.analytic_distribution:
                    analytic_distribution = budget_group_id.analytic_distribution

                # Preparar valores del gasto
                expense_vals = {
                    'date': expense_date,
                    'employee_id': employee_id.id,
                    'product_id': product_id.id,
                    'partner_id': partner_id.id,
                    'name': description or product_id.display_name,
                    'total_amount': total_amount,
                    'amount_tax_excluded': tax_excluded,
                    'tax_amount': tax_amount,
                    'amount_tax_excluded_description': tax_excluded_desc,
                    'company_id': company_id.id,
                    'payment_mode': self.payment_mode,
                }

                # Agregar campos opcionales
                if budget_group_id:
                    expense_vals['budget_group_id'] = budget_group_id.id
                
                if analytic_distribution:
                    expense_vals['analytic_distribution'] = analytic_distribution

                # Agrupar por referencia
                if reference not in expenses_by_reference:
                    expenses_by_reference[reference] = {
                        'employee_id': employee_id,
                        'company_id': company_id,
                        'expenses': [],
                        'accounting_date': accounting_date  # Guardar fecha de contabilización
                    }
                
                expenses_by_reference[reference]['expenses'].append(expense_vals)

            except Exception as e:
                errors.append(f"Fila {row_num}: Error al procesar - {str(e)}")
                continue

        # Obtener aprobador por defecto
        default_approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'hr_expense_import.default_expense_approver_id', 0
        ))
        if not default_approver_id:
            default_approver_id = 201

        # Crear reportes de gastos con sus gastos
        for reference, data in expenses_by_reference.items():
            try:
                # Crear el reporte de gastos (hr.expense.sheet)
                sheet_vals = {
                    'name': reference,
                    'employee_id': data['employee_id'].id,
                    'company_id': data['company_id'].id,
                }

                # Asignar aprobador por defecto
                if default_approver_id:
                    sheet_vals['user_id'] = default_approver_id

                # Agregar campos específicos del módulo hr_expense_credit_card
                if self.payment_mode == 'credit_card' and self.credit_card_id:
                    sheet_vals['credit_card_id'] = self.credit_card_id.id
                
                # Agregar campo agrupar_por_factura
                sheet_vals['agrupar_por_factura'] = self.agrupar_por_factura

                # Agregar campo documento_soporte
                sheet_vals['documento_soporte'] = self.documento_soporte

                # NUEVA FUNCIONALIDAD 3: Agregar accounting_date si existe
                if data.get('accounting_date'):
                    sheet_vals['accounting_date'] = data['accounting_date']

                # Crear gastos primero
                expense_ids = []
                for expense_vals in data['expenses']:
                    expense = self.env['hr.expense'].create(expense_vals)
                    expense_ids.append(expense.id)

                # Asociar gastos al reporte
                sheet_vals['expense_line_ids'] = [(6, 0, expense_ids)]

                # Crear el reporte
                expense_sheet = self.env['hr.expense.sheet'].create(sheet_vals)
                
                # NUEVA FUNCIONALIDAD 4: Aprobar el reporte automáticamente
                expense_sheet.action_approve_expense_sheets()
                
                created_sheets.append(expense_sheet.id)

                self.env.cr.commit()

            except Exception as e:
                errors.append(f"Error al crear reporte '{reference}': {str(e)}")
                self.env.cr.rollback()
                continue

        # Mostrar resultado
        if errors:
            error_msg = 'Errores durante la importación:\n\n' + '\n'.join(errors)
            raise UserError(error_msg)

        if not created_sheets:
            raise UserError(_("No se importaron reportes de gastos"))

        # Retornar a la vista de reportes creados
        return {
            'name': _('Reportes de Gastos Importados'),
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.sheet',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_sheets)],
            'target': 'current',
        }
