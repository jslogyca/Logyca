# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO

def _day_count_30_360(d1, d2):
    """
    Calcula días entre d1 y d2 bajo convención 30/360 (meses de 30 días).
    Ajusta días 31 a 30 en ambas fechas (30E/360 simple).
    """
    if not d1 or not d2:
        return 0
    y1, m1, day1 = d1.year, d1.month, d1.day
    y2, m2, day2 = d2.year, d2.month, d2.day
    if day1 == 31:
        day1 = 30
    if day2 == 31:
        day2 = 30
    return (y2 - y1) * 360 + (m2 - m1) * 30 + (day2 - day1)


MONTHS = [
    ('1', "ENERO"), ('2', "FEBRERO"), ('3', "MARZO"), ('4', "ABRIL"),
    ('5', "MAYO"), ('6', "JUNIO"), ('7', "JULIO"), ('8', "AGOSTO"),
    ('9', "SEPTIEMBRE"), ('10', "OCTUBRE"), ('11', "NOVIEMBRE"), ('12', "DICIEMBRE"),
]

class VacationReportWizard(models.TransientModel):
    _name = "vacation.report.wizard"
    _description = "Generador XLSX Vacaciones"

    year = fields.Integer(string="Año", required=True, default=lambda self: fields.Date.today().year)
    month = fields.Selection(MONTHS, string="Mes", required=True, default=lambda self: str(fields.Date.today().month))
    company_id = fields.Many2one("res.company", string="Compañía", required=True, default=lambda self: self.env.company)
    leave_type_id = fields.Many2one(
        "hr.leave.type", string="Tipo de Ausencia",
        domain=[("time_type", "=", "leave")], required=True
    )
    only_active_contracts = fields.Boolean(string="Solo contratos activos a la fecha de corte", default=True)

    def _get_period_bounds(self):
        self.ensure_one()
        y = int(self.year)
        m = int(self.month)
        date_from = date(y, m, 1)
        date_to = (date_from + relativedelta(months=1)) - relativedelta(days=1)
        prev_year_end = date(y - 1, 12, 31)
        return date_from, date_to, prev_year_end

    def _get_contract_for_employee(self, emp, at_date):
        Contract = self.env["hr.contract"]
        contracts = Contract.search([
            ("employee_id", "=", emp.id),
            ("company_id", "=", self.company_id.id),
            ("date_start", "<=", at_date),
            "|", ("date_end", "=", False), ("date_end", ">=", at_date),
        ], order="state desc, date_start desc", limit=1)
        if self.only_active_contracts and contracts and contracts.state not in ("open", "close"):
            return False
        return contracts[:1]

    def _sum_leave_days(self, emp, leave_type, date_from, date_to):
        Leave = self.env["hr.leave"]
        leaves = Leave.search([
            ("employee_id", "=", emp.id),
            ("holiday_status_id", "=", leave_type.id),
            ("state", "=", "validate"),
            ("request_date_from", "<=", date_to),
            ("request_date_to", ">=", date_from),
        ])
        total = 0.0
        for l in leaves:
            start = max(fields.Date.to_date(l.request_date_from), date_from)
            end = min(fields.Date.to_date(l.request_date_to), date_to)
            delta = (end - start).days + 1
            if l.number_of_days:
                total += min(l.number_of_days, delta)
            else:
                total += delta
        return total

    def _sum_allocations(self, emp, leave_type, date_to):
        Allocation = self.env["hr.leave.allocation"]
        allocs = Allocation.search([
            ("employee_id", "=", emp.id),
            ("holiday_status_id", "=", leave_type.id),
            ("state", "=", "validate"),
            ("allocation_type", "!=", "no"),
            ("date_to", "<=", date_to),
        ])
        return sum(a.number_of_days_display or a.number_of_days or 0.0 for a in allocs)

    def action_export_xlsx(self):
        self.ensure_one()
        date_from, date_to, prev_year_end = self._get_period_bounds()
        month_label = dict(MONTHS).get(self.month)

        out = BytesIO()
        import xlsxwriter
        wb = xlsxwriter.Workbook(out, {"in_memory": True})
        ws = wb.add_worksheet(f"{month_label} {self.year}")

        f_title = wb.add_format({"bold": True, "font_size": 14, "font_color": "#2c3e50"})
        f_subtle = wb.add_format({"font_size": 10, "font_color": "#7f8c8d"})
        f_header = wb.add_format({"bold": True, "bg_color": "#ecf0f1", "border": 1})
        f_cell = wb.add_format({"border": 1})
        f_num = wb.add_format({"border": 1, "num_format": "0.00"})
        f_bold = wb.add_format({"border": 1, "bold": True})

        ws.write(0, 0, "Compañía:", f_bold); ws.write(0, 1, self.company_id.display_name, f_cell)
        ws.write(1, 0, "Informe:", f_bold); ws.write(1, 1, f"VACACIONES CORTE {month_label}", f_cell)
        ws.write(2, 0, "Fecha:",   f_bold); ws.write(2, 1, fields.Date.to_string(date_to), f_cell)

        headers = [
            "No. DOCUMENTO","NOMBRE EMPLEADO","FECHA INGRESO","CÓDIGO ÁREA",
            "ÁREA FUNCIONAL","CARGO","SALARIO",
            "DIAS TOMADOS ENERO","DIAS TOMADOS FEBRERO","DIAS TOMADOS MARZO",
            "DIAS TOMADOS ABRIL","DIAS TOMADOS MAYO","DIAS TOMADOS JUNIO",
            "DIAS TOMADOS JULIO","DIAS TOMADOS AGOSTO","DIAS TOMADOS SEPTIEMBRE",
            "DIAS TOMADOS OCTUBRE","DIAS TOMADOS NOVIEMBRE","DIAS TOMADOS DICIEMBRE",
            f"TOTAL DÍAS TOMADOS {self.year}",
            "DIAS INICIAL","DÍA FIN",f"TOTAL DÍAS  {self.year}",
            f"VAC ACUMULADAS DIC {self.year - 1}",
            f"VAC ACUMULADAS {month_label} {self.year}",
            f"TOTAL VACACIONES CORTE {month_label} {self.year}",
            "SALDO TOTAL",
        ]
        start_row = 5
        for c, h in enumerate(headers):
            ws.write(start_row, c, h, f_header)

        Employee = self.env["hr.employee"]
        employees = Employee.search([("company_id", "=", self.company_id.id)], order="name")
        row = start_row + 1

        for emp in employees:
            contract = self._get_contract_for_employee(emp, date_to)
            if self.only_active_contracts and not contract:
                continue

            document = emp.identification_id or ""
            area_code = getattr(emp.department_id, "code", "") or ""
            area_name = emp.department_id.name if emp.department_id else ""
            job_name = emp.job_id.name if emp.job_id else ""
            hire_date_raw = getattr(emp, 'first_contract_date', None) or getattr(emp, 'create_date', None)
            hire_date_dt = fields.Date.to_date(hire_date_raw) if hire_date_raw else None
            hire_date = hire_date_dt  # for display we will str() it later
            salary = contract.wage if contract else 0.0

            days_by_month = []
            total_taken_ytd = 0.0
            for m in range(1, 12+1):
                m_start = date(self.year, m, 1)
                m_end = (m_start + relativedelta(months=1)) - relativedelta(days=1)
                val = self._sum_leave_days(emp, self.leave_type_id, m_start, m_end)
                days_by_month.append(val)
                if m <= int(self.month):
                    total_taken_ytd += val

            alloc_prev = self._sum_allocations(emp, self.leave_type_id, prev_year_end)
            taken_prev  = self._sum_leave_days(emp, self.leave_type_id, date(1900,1,1), prev_year_end)
            vac_acum_dic_prev_year = max(0.0, alloc_prev - taken_prev)

            alloc_cut = self._sum_allocations(emp, self.leave_type_id, date_to)
            taken_cut = self._sum_leave_days(emp, self.leave_type_id, date(1900,1,1), date_to)
            vac_acum_mes = max(0.0, alloc_cut - taken_cut)

            total_vac_corte = vac_acum_mes
            saldo_total = vac_acum_mes


            # Escribir columnas base (A..G) y los días por mes (H..S), y TOTAL DÍAS TOMADOS (T)
            col = 0
            ws.write(row, col, document, f_cell); col += 1
            ws.write(row, col, (emp.name or ""), f_cell); col += 1

            date_fmt = wb.add_format({"num_format": "dd/mm/yyyy", "border": 1})
            if hire_date_dt:
                ws.write_datetime(row, col, hire_date_dt, date_fmt)
            else:
                ws.write(row, col, "", f_cell)
            col += 1

            ws.write(row, col, area_code, f_cell); col += 1
            ws.write(row, col, area_name, f_cell); col += 1
            ws.write(row, col, job_name, f_cell); col += 1
            ws.write_number(row, col, salary or 0.0, f_num); col += 1

            for v in days_by_month:
                ws.write_number(row, col, v or 0.0, f_num); col += 1

            ws.write_number(row, col, total_taken_ytd or 0.0, f_bold); col += 1

            # Fechas de rango: 01/Enero/{year} hasta fin de mes seleccionado
            date_year_start = date(self.year, 1, 1)
            date_month_end = date_to  # último día del mes seleccionado
            dias_inicial = max(date_year_start, hire_date_dt) if hire_date_dt else date_year_start
            dia_fin = date_month_end
            # Total días entre las dos fechas (inclusive)
            total_dias_anio = _day_count_30_360(dias_inicial, dia_fin)

            # VAC ACUMULADAS DIC {año-1}: opción A (manual por empleado) o cálculo automático
            if getattr(emp, "x_vac_carry_prev_year", False):
                vac_acum_dic_prev_year = emp.x_vac_carry_prev_year
            else:
                vac_acum_dic_prev_year = max(0.0, alloc_prev - taken_prev)

            # VAC ACUMULADAS {mes año} = (TOTAL DÍAS  {year} * 15) / 360
            vac_acum_mes = (total_dias_anio * 15.0) / 360.0

            # Escribir hasta TOTAL DÍAS TOMADOS (T): ya escrito arriba en total_taken_ytd
            # Escribimos DIAS INICIAL (U) y DÍA FIN (V) como fechas, TOTAL DÍAS  {year} (W) como número
            date_fmt = wb.add_format({"num_format": "dd/mm/yyyy", "border": 1})
            ws.write_datetime(row, col, dias_inicial, date_fmt); col += 1
            ws.write_datetime(row, col, dia_fin, date_fmt); col += 1
            ws.write_number(row, col, total_dias_anio, f_num); col += 1

            # Columnas X (acum DIC prev) e Y (acum mes)
            ws.write_number(row, col, vac_acum_dic_prev_year, f_num); col += 1
            ws.write_number(row, col, vac_acum_mes, f_num); col += 1

            # Columna Z = (X + Y) - T  y Columna AA = G/30 * Z  (como fórmulas)
            # Determinamos la fila de Excel (1-based). Encabezados en fila 6 => primera fila de datos = 7
            col_T = 20  # índice base 0: "TOTAL DÍAS TOMADOS {year}" está en posición 20
            excel_row = row + 1
            col_X = 23  # VAC ACUMULADAS DIC prev
            col_Y = 24  # VAC ACUMULADAS {mes}
            col_Z = 25  # TOTAL VACACIONES CORTE {mes}
            col_AA = 26 # SALDO TOTAL
            col_G = 6   # SALARIO
            # Letras de columna según índice
            def col_letter(idx):
                # idx 0->A, 1->B ...
                letters = ""
                x = idx
                while True:
                    x, r = divmod(x, 26)
                    letters = chr(65 + r) + letters
                    if x == 0:
                        break
                    x -= 1
                return letters

            col_T = 19  # índice base 0: "TOTAL DÍAS TOMADOS {year}" está en posición 20
            T_ref = f"{col_letter(col_T)}{excel_row}"
            X_ref = f"{col_letter(col_X)}{excel_row}"
            Y_ref = f"{col_letter(col_Y)}{excel_row}"
            Z_ref = f"{col_letter(col_Z)}{excel_row}"
            G_ref = f"{col_letter(col_G)}{excel_row}"

            ws.write_formula(row, col, f"=({X_ref}+{Y_ref})-{T_ref}", f_bold); col += 1
            ws.write_formula(row, col, f"=({G_ref}/30)*{Z_ref}", f_bold); col += 1


            row += 1

        widths = [15, 35, 14, 12, 24, 24, 12] + [18]*12 + [22, 12, 10, 18, 24, 28, 34, 16]
        for i, w in enumerate(widths[:len(headers)]):
            ws.set_column(i, i, w)

        wb.close()
        out_value = out.getvalue()
        out.close()

        fname = f"VACACIONES_CORTE_{month_label}_{self.year}.xlsx"
        attachment = self.env["ir.attachment"].create({
            "name": fname,
            "type": "binary",
            "datas": base64.b64encode(out_value),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        })
        url = f"/web/content/{attachment.id}?download=true"
        return {
            "type": "ir.actions.act_url",
            "name": _("Descargar XLSX"),
            "url": url,
            "target": "self",
        }
