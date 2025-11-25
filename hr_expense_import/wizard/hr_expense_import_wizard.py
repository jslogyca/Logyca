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
        3. Validar que el grupo presupuestal existe
        4. Validar que la cuenta analítica existe
        5. Validar que existe configuración de producto para el proveedor
        6. Validar que no exista ya un reporte con la misma referencia
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
            budget_group_name = str(fila[8]) if len(fila) > 8 and fila[8] else ''
            analytic_name = str(fila[9]) if len(fila) > 9 and fila[9] else ''
            total_amount = float(fila[10]) if len(fila) > 10 and fila[10] else 0.0
            tax_excluded = float(fila[11]) if len(fila) > 11 and fila[11] else 0.0
            tax_amount = float(fila[12]) if len(fila) > 12 and fila[12] else 0.0

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
                        'count': 0
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
                        if not product_config:
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

            # VALIDACIÓN 5: Verificar que el grupo presupuestal existe
            if budget_group_name and company_id:
                budget_group = self.env['logyca.budget_group'].search([
                    ('name', '=', budget_group_name),
                    ('company_id', '=', company_id.id)
                ], limit=1)
                if not budget_group:
                    errors.append(
                        f"Fila {row_num}: Grupo Presupuestal '{budget_group_name}' "
                        f"no existe para la compañía '{company_id.name}'"
                    )

            # VALIDACIÓN 6: Verificar que la cuenta analítica existe
            if analytic_name and company_id:
                analytic_account = self.env['account.analytic.account'].search([
                    ('name', '=', analytic_name.strip()),
                    '|',
                    ('company_id', '=', company_id.id),
                    ('company_id', '=', False)
                ], limit=1)
                if not analytic_account:
                    errors.append(f"Fila {row_num}: Cuenta Analítica '{analytic_name}' no existe")

        # VALIDACIÓN 7: Verificar si ya existen reportes con las mismas referencias
        for reference, ref_data in references_dict.items():
            if reference:
                company_name = ref_data['company_name']
                employee_name = ref_data['employee_name']
                
                company_id = self.env['res.company'].search([
                    ('name', '=', company_name)
                ], limit=1)
                
                employee_id = self.env['hr.employee'].search([
                    ('name', '=', employee_name)
                ], limit=1)

                if company_id and employee_id:
                    existing_sheet = self.env['hr.expense.sheet'].search([
                        ('name', '=', reference),
                        ('employee_id', '=', employee_id.id),
                        ('company_id', '=', company_id.id)
                    ], limit=1)
                    
                    if existing_sheet:
                        errors.append(
                            f"CRÍTICO: Ya existe un Reporte de Gastos con la referencia '{reference}' "
                            f"para el empleado {employee_id.name} (ID: {existing_sheet.id})"
                        )

        # VALIDACIÓN 8: Validar modo de pago y tarjeta de crédito
        if self.payment_mode == 'credit_card' and not self.credit_card_id:
            errors.append("Debe seleccionar una tarjeta de crédito cuando el modo de pago es 'Tarjeta de Crédito'")

        # Construir mensaje de resultado
        result_msg = []
        
        if errors:
            result_msg.append("=" * 80)
            result_msg.append("ERRORES ENCONTRADOS:")
            result_msg.append("=" * 80)
            for error in errors:
                result_msg.append(f"❌ {error}")
            result_msg.append("")

        if warnings:
            result_msg.append("=" * 80)
            result_msg.append("ADVERTENCIAS:")
            result_msg.append("=" * 80)
            for warning in warnings:
                result_msg.append(f"⚠️ {warning}")
            result_msg.append("")

        if not errors and not warnings:
            result_msg.append("=" * 80)
            result_msg.append("✅ VALIDACIÓN EXITOSA")
            result_msg.append("=" * 80)
            result_msg.append(f"Total de referencias encontradas: {len(references_dict)}")
            result_msg.append(f"Total de gastos a importar: {row_num - 1}")
            result_msg.append("")
            result_msg.append("El archivo está listo para ser importado.")
        elif not errors:
            result_msg.append("=" * 80)
            result_msg.append("⚠️ VALIDACIÓN COMPLETADA CON ADVERTENCIAS")
            result_msg.append("=" * 80)
            result_msg.append("Se puede proceder con la importación, pero revise las advertencias.")

        self.validation_result = "\n".join(result_msg)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.expense.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_expenses(self):
        """
        Importar los reportes de gastos con sus gastos asociados
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
        created_sheets = []
        
        # Diccionario para agrupar gastos por referencia (reporte)
        expenses_by_reference = {}

        row_num = 1
        for fila in record_list:
            row_num += 1
            if not fila or not any(fila):  # Si la fila está vacía
                continue

            try:
                # Extraer datos de la fila
                company_name = str(fila[0]) if fila[0] else ''
                date_value = fila[1] if len(fila) > 1 else ''
                reference = str(fila[2]) if len(fila) > 2 and fila[2] else ''
                partner_vat = str(fila[3]) if len(fila) > 3 and fila[3] else ''
                description = str(fila[4]) if len(fila) > 4 and fila[4] else ''
                tax_excluded_desc = str(fila[5]) if len(fila) > 5 and fila[5] else ''
                partner_name = str(fila[6]) if len(fila) > 6 and fila[6] else ''
                employee_name = str(fila[7]) if len(fila) > 7 and fila[7] else ''
                budget_group_name = str(fila[8]) if len(fila) > 8 and fila[8] else ''
                analytic_name = str(fila[9]) if len(fila) > 9 and fila[9] else ''
                total_amount = float(fila[10]) if len(fila) > 10 and fila[10] else 0.0
                tax_excluded = float(fila[11]) if len(fila) > 11 and fila[11] else 0.0
                tax_amount = float(fila[12]) if len(fila) > 12 and fila[12] else 0.0

                # Limpiar NIT
                suffix = ".0"
                if partner_vat.endswith(suffix):
                    partner_vat = partner_vat[:-len(suffix)]
                if employee_name.endswith(suffix):
                    employee_name = employee_name[:-len(suffix)]                    
                if reference.endswith(suffix):
                    reference = reference[:-len(suffix)]                    
                if description.endswith(suffix):
                    description = description[:-len(suffix)]                    

                # Buscar compañía
                company_id = self.env['res.company'].search([
                    ('name', '=', company_name)
                ], limit=1) if company_name else self.env.company

                # Buscar proveedor
                partner_id = self.env['res.partner'].search([
                    ('vat', '=', partner_vat),
                    ('parent_id', '=', False)
                ], limit=1)

                if not partner_id:
                    errors.append(f"Fila {row_num}: No se encontró el proveedor con NIT '{partner_vat}'")
                    continue

                # Buscar empleado
                employee_id = self.env['hr.employee'].search([
                    ('identification_id', '=', employee_name)
                ], limit=1)

                if not employee_id:
                    errors.append(f"Fila {row_num}: No se encontró el empleado '{employee_name}'")
                    continue

                # Buscar grupo presupuestal
                budget_group_id = self.env['logyca.budget_group'].search([
                    ('name', '=', budget_group_name),
                    ('company_id', '=', company_id.id)
                ], limit=1) if budget_group_name else False

                # Buscar cuenta analítica
                analytic_id = self.env['account.analytic.account'].search([
                    ('name', '=', analytic_name.strip()),
                    '|',
                    ('company_id', '=', company_id.id),
                    ('company_id', '=', False)
                ], limit=1) if analytic_name else False

                # Buscar producto usando la lógica de partner.product.purchase
                # Similar a la lógica del wizard de sale.order.import
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
                
                if not product_id:
                    errors.append(
                        f"Fila {row_num}: No se encontró configuración de producto para el proveedor "
                        f"'{partner_id.name}' en la compañía '{company_id.name}'"
                    )
                    continue

                # Convertir fecha
                expense_date = datetime.today().date()
                if date_value:
                    try:
                        if isinstance(date_value, float):
                            # Excel guarda fechas como números
                            expense_date = xlrd.xldate_as_datetime(date_value, xls_tmp_file.datemode).date()
                        else:
                            expense_date = datetime.strptime(str(date_value), '%Y-%m-%d').date()
                    except:
                        pass  # Usar fecha actual si hay error

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
                        'expenses': []
                    }
                
                expenses_by_reference[reference]['expenses'].append(expense_vals)

            except Exception as e:
                errors.append(f"Fila {row_num}: Error al procesar - {str(e)}")
                continue

        # Obtener aprobador por defecto de la configuración
        default_approver_id = int(self.env['ir.config_parameter'].sudo().get_param(
            'hr_expense_import.default_expense_approver_id', 0
        ))
        if not default_approver_id:
            default_approver_id=201
        # Crear reportes de gastos con sus gastos
        for reference, data in expenses_by_reference.items():
            try:
                # Crear el reporte de gastos (hr.expense.sheet)
                sheet_vals = {
                    'name': reference,
                    'employee_id': data['employee_id'].id,
                    'company_id': data['company_id'].id,
                }

                # Asignar aprobador por defecto si está configurado
                if default_approver_id:
                    sheet_vals['user_id'] = default_approver_id

                # Agregar campos específicos del módulo hr_expense_credit_card
                if self.payment_mode == 'credit_card' and self.credit_card_id:
                    sheet_vals['credit_card_id'] = self.credit_card_id.id

                # Crear gastos primero
                expense_ids = []
                for expense_vals in data['expenses']:
                    expense = self.env['hr.expense'].create(expense_vals)
                    expense_ids.append(expense.id)

                # Asociar gastos al reporte
                sheet_vals['expense_line_ids'] = [(6, 0, expense_ids)]

                # Crear el reporte
                expense_sheet = self.env['hr.expense.sheet'].create(sheet_vals)
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
