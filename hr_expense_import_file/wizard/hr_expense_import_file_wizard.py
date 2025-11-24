
# -*- coding: utf-8 -*-

import base64
import tempfile
from datetime import datetime

import xlrd

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrExpenseImportFileWizard(models.TransientModel):
    _name = "hr.expense.import.file.wizard"
    _description = "Expense Import File Wizard"

    file_data = fields.Binary(string="Archivo", required=True)
    filename = fields.Char(string="Nombre del archivo")
    validation_result = fields.Text(string="Resultado de validación", readonly=True)

    payment_mode = fields.Selection(
        selection=lambda self: self.env["hr.expense"]._fields["payment_mode"].selection,
        string="Pagador",
        required=True,
    )
    credit_card_id = fields.Many2one(
        comodel_name="credit.card",
        string="Tarjeta de Crédito",
    )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _read_xls_rows(self):
        """Lee el archivo Excel y devuelve una lista de filas (saltando encabezados)."""
        self.ensure_one()
        if not self.file_data:
            raise ValidationError(_("No se encuentra un archivo, por favor cargue uno."))

        try:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)
            tmp_file.write(base64.b64decode(self.file_data))
            tmp_file.close()
            book = xlrd.open_workbook(tmp_file.name)
        except Exception as e:
            raise ValidationError(
                _("No se puede leer el archivo. Verifique que el formato sea el correcto.\n\nDetalle técnico: %s") % e
            )

        sheet = book.sheet_by_index(0)
        # Saltar fila 0 (título PLANTILLA) y fila 1 (encabezados)
        record_list = [sheet.row_values(i) for i in range(1, sheet.nrows)]
        return book, record_list

    def _as_str(self, value):
        return (str(value).strip()) if value not in (False, None) else ""

    def _float_or_error(self, value, row_num, field_label, errors):
        if value in (False, None, "", " "):
            return 0.0
        try:
            return float(value)
        except Exception:
            errors.append(
                _("Fila %(row)s: El valor de '%(field)s' debe ser numérico, se recibió '%(val)s'.") % {
                    "row": row_num,
                    "field": field_label,
                    "val": value,
                }
            )
            return 0.0

    def _parse_date(self, book, raw_value, row_num, errors):
        if not raw_value:
            errors.append(_("Fila %s: La fecha es obligatoria.") % row_num)
            return False
        try:
            # Excel date numérico
            if isinstance(raw_value, float):
                dt = datetime(*xlrd.xldate_as_tuple(raw_value, book.datemode))
                return dt.date()
            # String en formato permitido por Odoo
            if isinstance(raw_value, str):
                return fields.Date.from_string(raw_value)
            # Ya viene como date/datetime
            if hasattr(raw_value, "date"):
                return raw_value.date() if hasattr(raw_value, "date") else raw_value
            return raw_value
        except Exception:
            errors.append(
                _("Fila %(row)s: La fecha '%(val)s' no tiene un formato válido.") % {
                    "row": row_num,
                    "val": raw_value,
                }
            )
            return False

    # -------------------------------------------------------------------------
    # Validaciones
    # -------------------------------------------------------------------------

    def action_validate_data(self):
        """
        Valida el archivo sin crear registros:
        - Compañía
        - Empleado
        - Proveedor (NIT + parent_id = False)
        - Grupo presupuestal
        - Cuenta analítica
        - Configuración partner.product.purchase (product_id)
        - Consistencia de referencia por compañía/empleado
        """
        book, record_list = self._read_xls_rows()

        errors = []
        warnings = []
        row_num = 1  # fila lógica del Excel (sin contar las 2 encabezado)

        # Para validar coherencia por referencia
        ref_map = {}  # ref -> (company_id, employee_id)

        for fila in record_list:
            row_num += 1
            # Si la fila está totalmente vacía, la ignoro
            if not any(fila):
                continue

            # Mapeo columnas (según tu plantilla)
            # 0: Compañía (hr.expense - company_id.name)
            # 1: Fecha  (hr.expense - date)
            # 2: Referencia (hr.expense.sheet - name)
            # 3: NIT Proveedor (hr.expense - partner_id)
            # 4: Notas internas (hr.expense - description)
            # 5: Descripción exento de IVA (hr.expense - amount_tax_excluded_description)
            # 6: Proveedor  (hr.expense - partner_id.name)
            # 7: Empleado (hr.expense - employee_id)
            # 8: Grupo Presupuestal (hr.expense - budget_group_id)
            # 9: Cuenta Analítica (hr.expense - analytic_distribution)
            # 10: Total (hr.expense - total_amount)
            # 11: exento de IVA (hr.expense - amount_tax_excluded)
            # 12: IVA (hr.expense - tax_amount)
            company_name = self._as_str(fila[0])
            date_raw = fila[1]
            reference = self._as_str(fila[2])
            supplier_vat = self._as_str(fila[3])
            # internal_notes = self._as_str(fila[4])
            excluded_desc = self._as_str(fila[5])
            supplier_name = self._as_str(fila[6])
            employee_name = self._as_str(fila[7])
            budget_group_name = self._as_str(fila[8])
            analytic_name = self._as_str(fila[9])

            total_val = fila[10] if len(fila) > 10 else 0.0
            excluded_val = fila[11] if len(fila) > 11 else 0.0
            tax_val = fila[12] if len(fila) > 12 else 0.0

            # Limpiar NIT
            suffix = ".0"
            if supplier_vat.endswith(suffix):
                supplier_vat = supplier_vat[:-len(suffix)]            
            if employee_name.endswith(suffix):
                employee_name = employee_name[:-len(suffix)]            
            if reference.endswith(suffix):
                reference = reference[:-len(suffix)]            

            # -----------------------------------------------------------------
            # Compañía
            # -----------------------------------------------------------------
            if company_name:
                company = self.env["res.company"].search(
                    [("name", "=", company_name)], limit=1
                )
                if not company:
                    errors.append(
                        _("Fila %(row)s: La compañía '%(comp)s' no existe.") % {
                            "row": row_num,
                            "comp": company_name,
                        }
                    )
            else:
                company = self.env.company
                warnings.append(
                    _("Fila %s: No se indicó compañía, se asumirá la compañía actual.") % row_num
                )

            # -----------------------------------------------------------------
            # Fecha
            # -----------------------------------------------------------------
            expense_date = self._parse_date(book, date_raw, row_num, errors)

            # -----------------------------------------------------------------
            # Empleado
            # -----------------------------------------------------------------
            employee = False
            if employee_name:
                domain = [("identification_id", "=", employee_name)]
                # if company:
                #     domain.append(("company_id", "in", [company.id, False]))
                employees = self.env["hr.employee"].search(domain)
                if not employees:
                    errors.append(
                        _("Fila %(row)s: No se encontró empleado '%(emp)s' en la compañía '%(comp)s'.") % {
                            "row": row_num,
                            "emp": employee_name,
                            "comp": company_name or company.display_name,
                        }
                    )
                elif len(employees) > 1:
                    warnings.append(
                        _("Fila %(row)s: Se encontraron múltiples empleados con el nombre '%(emp)s'; se usará '%(first)s'.") % {
                            "row": row_num,
                            "emp": employee_name,
                            "first": employees[0].display_name,
                        }
                    )
                    employee = employees[0]
                else:
                    employee = employees
            else:
                errors.append(_("Fila %s: El empleado es obligatorio.") % row_num)

            # -----------------------------------------------------------------
            # Proveedor (por NIT y parent_id = False)
            # -----------------------------------------------------------------
            partner = False
            if supplier_vat:
                partners = self.env["res.partner"].search(
                    [("vat", "=", supplier_vat), ("parent_id", "=", False)]
                )
                if not partners:
                    errors.append(
                        _("Fila %(row)s: No se encontró proveedor con NIT '%(vat)s'.") % {
                            "row": row_num,
                            "vat": supplier_vat,
                        }
                    )
                elif len(partners) > 1:
                    warnings.append(
                        _("Fila %(row)s: Se encontraron múltiples proveedores con NIT '%(vat)s'; se usará '%(name)s'.") % {
                            "row": row_num,
                            "vat": supplier_vat,
                            "name": partners[0].display_name,
                        }
                    )
                    partner = partners[0]
                else:
                    partner = partners
            else:
                warnings.append(
                    _("Fila %s: No se indicó NIT de proveedor; el gasto se creará sin proveedor.") % row_num
                )

            # Validación de nombre de proveedor (no crítica)
            if supplier_name and partner and supplier_name.strip().upper() != partner.name.strip().upper():
                warnings.append(
                    _("Fila %(row)s: El nombre del proveedor en la plantilla ('%(sup)s') no coincide con el nombre del partner '%(name)s'.") % {
                        "row": row_num,
                        "sup": supplier_name,
                        "name": partner.name,
                    }
                )

            # -----------------------------------------------------------------
            # Grupo Presupuestal
            # -----------------------------------------------------------------
            budget_group = False
            if budget_group_name:
                domain = [("name", "=", budget_group_name)]
                if company:
                    domain.append(("company_id", "=", company.id))
                budget_group = self.env["logyca.budget_group"].search(domain, limit=1)
                if not budget_group:
                    errors.append(
                        _("Fila %(row)s: Grupo presupuestal '%(grp)s' no existe para la compañía '%(comp)s'.") % {
                            "row": row_num,
                            "grp": budget_group_name,
                            "comp": company_name or company.display_name,
                        }
                    )

            # -----------------------------------------------------------------
            # Cuenta analítica
            # -----------------------------------------------------------------
            if analytic_name:
                analytic = self.env["account.analytic.account"].search(
                    [
                        ("name", "=", analytic_name.strip()),
                        "|",
                        ("company_id", "=", company.id if company else False),
                        ("company_id", "=", False),
                    ],
                    limit=1,
                )
                if not analytic:
                    errors.append(
                        _("Fila %(row)s: La cuenta analítica '%(ana)s' no existe.") % {
                            "row": row_num,
                            "ana": analytic_name,
                        }
                    )

            # -----------------------------------------------------------------
            # Montos
            # -----------------------------------------------------------------
            total_amount = self._float_or_error(total_val, row_num, "Total", errors)
            excluded_amount = self._float_or_error(excluded_val, row_num, "Exento de IVA", errors)
            tax_amount = self._float_or_error(tax_val, row_num, "IVA", errors)

            if total_amount <= 0.0:
                warnings.append(
                    _("Fila %s: El Total es 0 o negativo.") % row_num
                )
            if excluded_amount < 0.0:
                warnings.append(
                    _("Fila %s: El Exento de IVA es negativo.") % row_num
                )
            if tax_amount < 0.0:
                warnings.append(
                    _("Fila %s: El IVA es negativo.") % row_num
                )

            # -----------------------------------------------------------------
            # Configuración partner.product.purchase para producto (tipo GA)
            # -----------------------------------------------------------------
            if partner and company:
                ppp = self.env["partner.product.purchase"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("company_id", "=", company.id),
                        ("product_type", "=", "ga"),
                    ],
                    limit=1,
                )
                if not ppp:
                    errors.append(
                        _("Fila %(row)s: No existe configuración partner.product.purchase de tipo 'Gasto (ga)' para el proveedor '%(sup)s' y compañía '%(comp)s'.") % {
                            "row": row_num,
                            "sup": partner.display_name,
                            "comp": company_name or company.display_name,
                        }
                    )

            # -----------------------------------------------------------------
            # Coherencia de referencia por compañía/empleado
            # -----------------------------------------------------------------
            if reference:
                key = reference.strip()
                pair = (company.id if company else False, employee.id if employee else False)
                if key not in ref_map:
                    ref_map[key] = pair
                # else:
                #     if ref_map[key] != pair:
                #         errors.append(
                #             _("Fila %(row)s: La referencia '%(ref)s' ya fue usada con otra combinación de compañía/empleado.") % {
                #                 "row": row_num,
                #                 "ref": reference,
                #             }
                #         )

        # ---------------------------------------------------------------------
        # Construcción del resultado
        # ---------------------------------------------------------------------
        result_message = "=== RESULTADO DE LA VALIDACIÓN ===\n\n"

        if not errors and not warnings:
            result_message += "✓ VALIDACIÓN EXITOSA\n\n"
            result_message += "Todos los datos son correctos. Puede proceder con la importación.\n"
        else:
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
            result_message += "Por favor corrija los errores antes de importar.\n"

        self.validation_result = result_message

        if errors:
            # Igual que el wizard de compras: si hay errores => excepción
            raise ValidationError(result_message)

        # Si solo hay advertencias o nada, no se lanza excepción
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    # -------------------------------------------------------------------------
    # Importación
    # -------------------------------------------------------------------------

    def action_import_expenses(self):
        """
        Importa los datos creando:
        - hr.expense.sheet (agrupado por Referencia + Compañía + Empleado)
        - hr.expense vinculados al sheet
        """
        # Primero, ejecutar la validación (si hay errores, aborta)
        self.action_validate_data()

        book, record_list = self._read_xls_rows()

        ExpenseSheet = self.env["hr.expense.sheet"]
        Expense = self.env["hr.expense"]
        PartnerProductPurchase = self.env["partner.product.purchase"]

        sheets_created = ExpenseSheet.browse()
        expenses_created = Expense.browse()

        # Mapa para reutilizar sheets: clave = (company_id, employee_id, reference)
        sheet_map = {}

        row_num = 1
        for fila in record_list:
            row_num += 1
            if not any(fila):
                continue

            company_name = self._as_str(fila[0])
            date_raw = fila[1]
            reference = self._as_str(fila[2])
            supplier_vat = self._as_str(fila[3])
            internal_notes = self._as_str(fila[4])
            excluded_desc = self._as_str(fila[5])
            supplier_name = self._as_str(fila[6])
            employee_name = self._as_str(fila[7])
            budget_group_name = self._as_str(fila[8])
            analytic_name = self._as_str(fila[9])

            total_val = fila[10] if len(fila) > 10 else 0.0
            excluded_val = fila[11] if len(fila) > 11 else 0.0

            # Limpiar NIT
            suffix = ".0"
            if supplier_vat.endswith(suffix):
                supplier_vat = supplier_vat[:-len(suffix)]            
            if employee_name.endswith(suffix):
                employee_name = employee_name[:-len(suffix)]
            if reference.endswith(suffix):
                reference = reference[:-len(suffix)]                 

            # -----------------------------------------------------------------
            # Compañía
            # -----------------------------------------------------------------
            if company_name:
                company = self.env["res.company"].search(
                    [("name", "=", company_name)], limit=1
                )
                if not company:
                    raise UserError(
                        _("Fila %(row)s: La compañía '%(comp)s' no existe (no debería ocurrir si se validó antes).") % {
                            "row": row_num,
                            "comp": company_name,
                        }
                    )
            else:
                company = self.env.company

            # -----------------------------------------------------------------
            # Fecha
            # -----------------------------------------------------------------
            expense_date = self._parse_date(book, date_raw, row_num, [])
            if not expense_date:
                raise UserError(
                    _("Fila %s: La fecha no es válida (no debería ocurrir si se validó antes).") % row_num
                )

            # -----------------------------------------------------------------
            # Empleado
            # -----------------------------------------------------------------
            employee = False
            if employee_name:
                domain = [("identification_id", "=", employee_name)]
                # if company:
                #     domain.append(("company_id", "in", [company.id, False]))

                employees = self.env["hr.employee"].search(domain, limit=1)
                if not employees:
                    raise UserError(
                        _("Fila %(row)s: No se encontró empleado '%(emp)s' (no debería ocurrir si se validó antes).") % {
                            "row": row_num,
                            "emp": employee_name,
                        }
                    )
                employee = employees
            else:
                raise UserError(
                    _("Fila %s: El empleado es obligatorio (no debería ocurrir si se validó antes).") % row_num
                )

            # -----------------------------------------------------------------
            # Proveedor
            # -----------------------------------------------------------------
            partner = False
            if supplier_vat:
                partner = self.env["res.partner"].search(
                    [("vat", "=", supplier_vat), ("parent_id", "=", False)], limit=1
                )

            # -----------------------------------------------------------------
            # Grupo Presupuestal
            # -----------------------------------------------------------------
            budget_group = False
            if budget_group_name:
                domain = [("name", "=", budget_group_name)]
                if company:
                    domain.append(("company_id", "=", company.id))
                budget_group = self.env["logyca.budget_group"].search(domain, limit=1)

            # -----------------------------------------------------------------
            # Cuenta analítica / distribución
            # -----------------------------------------------------------------
            analytic_distribution = {}
            if budget_group and getattr(budget_group, "analytic_distribution", False):
                analytic_distribution = budget_group.analytic_distribution

            # -----------------------------------------------------------------
            # Montos
            # -----------------------------------------------------------------
            total_amount = float(total_val or 0.0)
            excluded_amount = float(excluded_val or 0.0)

            # -----------------------------------------------------------------
            # partner.product.purchase -> product_id
            # -----------------------------------------------------------------
            product = False
            if partner and company:
                ppp = PartnerProductPurchase.search(
                    [
                        ("partner_id", "=", partner.id),
                        ("company_id", "=", company.id),
                        ("product_type", "=", "ga"),
                    ],
                    limit=1,
                )
                if not ppp:
                    raise UserError(
                        _("Fila %(row)s: No existe configuración partner.product.purchase de tipo 'Gasto (ga)' para el proveedor '%(sup)s'.") % {
                            "row": row_num,
                            "sup": partner.display_name,
                        }
                    )
                product = ppp.product_id

            # -----------------------------------------------------------------
            # Crear/obtener hoja de gastos (sheet) por referencia + compañía + empleado
            # -----------------------------------------------------------------
            # ref_key = (company.id, employee.id, reference or "SIN-REFERENCIA")
            ref_key = (company.id, reference or "SIN-REFERENCIA")
            sheet = sheet_map.get(ref_key)
            if not sheet:
                sheet_vals = {
                    "name": reference or _("Reporte de gastos %s") % employee.name,
                    "employee_id": employee.id,
                    "company_id": company.id,
                }
                if self.payment_mode == "credit_card" and self.credit_card_id:
                    sheet_vals["credit_card_id"] = self.credit_card_id.id
                sheet = ExpenseSheet.create(sheet_vals)
                sheet_map[ref_key] = sheet
                sheets_created |= sheet

            # -----------------------------------------------------------------
            # Crear gasto (hr.expense)
            # -----------------------------------------------------------------
            expense_vals = {
                "name": excluded_desc or internal_notes or supplier_name or reference or _("Gasto importado"),
                "description": internal_notes,
                "employee_id": employee.id,
                "company_id": company.id,
                "date": expense_date,
                "quantity": 1.0,
                "total_amount": total_amount,
                "sheet_id": sheet.id,
                "budget_group_id": budget_group.id if budget_group else False,
                "analytic_distribution": analytic_distribution,
                "payment_mode": self.payment_mode,
            }
            if partner:
                expense_vals["partner_id"] = partner.id
            if product:
                expense_vals["product_id"] = product.id
            if excluded_amount:
                expense_vals["amount_tax_excluded"] = excluded_amount
            if excluded_desc:
                expense_vals["amount_tax_excluded_description"] = excluded_desc
            expense = Expense.create(expense_vals)
            expenses_created |= expense

        action = {
            "type": "ir.actions.act_window",
            "name": _("Reportes de gastos importados"),
            "res_model": "hr.expense.sheet",
            "view_mode": "tree,form",
            "domain": [("id", "in", sheets_created.ids)],
        }
        return action
