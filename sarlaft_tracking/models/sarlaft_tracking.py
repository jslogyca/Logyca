import base64
import csv
import io
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SarlaftTracking(models.Model):
    """Model to track SARLAFT queries for partners and employees."""

    _name = "sarlaft.tracking"
    _description = "SARLAFT Tracking"
    _order = "query_date desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "display_name"

    # Core fields
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        ondelete="cascade",
        required=True,
        help="Related partner (customer/supplier)",
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        ondelete="cascade",
        readonly=True,
        store=True,
        help="Related employee",
    )
    query_date = fields.Date(
        string="Query Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        help="Date when the SARLAFT query was performed",
    )
    next_query_date = fields.Date(
        string="Next Query Date",
        tracking=True,
        readonly=True,
        compute="_compute_next_query_date",
        store=True,
        help="Date for the next SARLAFT query",
    )
    approved = fields.Boolean(
        string="Approved",
        tracking=True,
        compute="_compute_approved",
        store=True,
        help="Indicates if the SARLAFT query was approved",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="Company that performed the query",
    )
    ident_type = fields.Many2one(
        "l10n_latam.identification.type",
        string="Identification Type",
        related="partner_id.l10n_latam_identification_type_id",
        readonly=True,
        help="Type of identification document",
    )
    ident_number = fields.Char(
        string="Identification Number",
        related="partner_id.vat",
        readonly=False,
        store=True,
        help="Identification document number",
    )
    result_risks = fields.Char(
        string="Risk Level",
        required=True,
        tracking=True,
        help="Risk level determined from the query",
    )
    high_risk = fields.Char(
        string="High Risk",
        help="High risk details",
    )
    medium_risk = fields.Char(
        string="Medium Risk",
        help="Medium risk details",
    )
    low_risk = fields.Char(
        string="Low Risk",
        help="Low risk details",
    )
    information = fields.Text(
        string="Additional Information",
        help="Additional information about the query",
    )
    comments = fields.Text(
        string="Comments",
        help="Additional comments about the query",
    )
    error_sources = fields.Char(
        string="Error Sources",
        help="Sources of errors found during the query",
    )
    result_link = fields.Char(
        string="Result Link",
        required=True,
        help="URL link to the detailed query result",
    )

    # Computed fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute="_compute_is_overdue",
        store=True,
        help="True if next query date has passed",
    )
    days_to_next_query = fields.Integer(
        string="Days to Next Query",
        compute="_compute_days_to_next_query",
        store=True,
        help="Number of days until next query",
    )

    # Compute methods

    @api.depends("partner_id", "employee_id")
    def _compute_display_name(self):
        """Compute display name based on partner/employee."""
        for record in self:
            if record.employee_id:
                name = record.employee_id.name
            elif record.partner_id:
                name = record.partner_id.name
            else:
                name = record.ident_number or "Unknown"
            record.display_name = name

    @api.depends("next_query_date")
    def _compute_is_overdue(self):
        """Compute if the record is overdue for next query."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = (
                record.next_query_date and record.next_query_date <= today
            )

    @api.depends("next_query_date")
    def _compute_days_to_next_query(self):
        """Compute days remaining until next query."""
        today = fields.Date.context_today(self)
        for record in self:
            if record.next_query_date:
                delta = record.next_query_date - today
                record.days_to_next_query = delta.days
            else:
                record.days_to_next_query = 0

    @api.depends("result_risks")
    def _compute_approved(self):
        """Compute if the query result is approved based on risk level."""
        for record in self:
            record.approved = (
                record.result_risks and record.result_risks.lower() == "ninguno"
            )

    @api.depends("query_date")
    def _compute_next_query_date(self):
        """Compute the next query date based on the current query date."""
        days_param = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sarlaft_tracking.next_query_days", default="365")
        )
        for record in self:
            if record.query_date:
                record.next_query_date = record.query_date + timedelta(days=days_param)
            else:
                query_date = fields.Date.context_today(self)
                record.query_date = query_date
                record.next_query_date = query_date + timedelta(days=days_param)

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Update employee_id based on selected partner."""
        for record in self:
            record.employee_id = record._get_employee()

    # Auxiliary methods

    def _get_employee(self):
        """Get the employee associated with the current record."""
        self.ensure_one()
        employee = False
        if self.partner_id and self.partner_id.employee_ids:
            employee_ids = self.partner_id.employee_ids.filtered(lambda e: e.active)
            employee = employee_ids[0] if employee_ids else False
        return employee

    def _translate_fields(self, fields):
        """Return fields that need translation."""
        translated = {
            "ident_number": _("Identification Number"),
            "partner_id": _("Partner"),
            "result_risks": _("Risk Level"),
            "high_risk": _("High Risk"),
            "medium_risk": _("Medium Risk"),
            "low_risk": _("Low Risk"),
            "information": _("Additional Information"),
            "query_date": _("Query Date"),
            "comments": _("Comments"),
            "error_sources": _("Error Sources"),
            "result_link": _("Result Link"),
        }
        return [translated.get(field, field) for field in fields]

    # Constraints methods

    @api.constrains("query_date", "next_query_date")
    def _check_dates(self):
        """Validate that next query date is after query date."""
        for record in self:
            if (
                record.query_date
                and record.next_query_date
                and record.next_query_date <= record.query_date
            ):
                raise ValidationError(
                    _("Next query date must be after the current query date")
                )

    # Overridden methods

    def name_get(self):
        """Return a more descriptive name for the record."""
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

    @api.model
    def load(self, fields, data):
        """
        Try to resolve partner by VAT ('ident_number') and then by name ('partner_id' received as text).
        Exclude from import the rows without a match.
        Optionally send an email with a CSV of omitted rows when coming from the import wizard (not dry-run).
        """
        if "ident_number" in fields and "partner_id" in fields:
            idx_vat = fields.index("ident_number")
            idx_partner = fields.index("partner_id")

            Partner = self.env["res.partner"].sudo()

            vats = {row[idx_vat] for row in data if row[idx_vat]}
            vat2partner = {}
            if vats:
                partners_vat = Partner.search([("vat", "in", list(vats))])
                vat2partner = {p.vat: p for p in partners_vat}

            names = {row[idx_partner] for row in data if row[idx_partner]}
            name2pid = {}
            for name in names:
                res = Partner.name_search(name, operator="ilike", limit=1)
                if res:
                    name2pid[name] = res[0][1]

            ok_rows, not_found = [], []
            for row in data:
                vat = row[idx_vat]
                name = row[idx_partner]
                partner_id = False

                if vat and vat in vat2partner:
                    partner_id = vat2partner[vat].name
                elif name and name in name2pid:
                    partner_id = name2pid[name]

                if partner_id:
                    row[idx_partner] = partner_id
                    ok_rows.append(row)
                else:
                    not_found.append(list(row))

            data = ok_rows

            if (
                not_found
                and self.env.context.get("import_file")
                and not self.env.context.get("import_dryrun")
            ):
                try:
                    buf = io.StringIO()
                    writer = csv.writer(buf)
                    user = self.env.user
                    columns = self.with_context(lang=user.lang)._translate_fields(
                        fields
                    )
                    writer.writerow(columns)
                    writer.writerows(not_found)
                    payload = base64.b64encode(buf.getvalue().encode("utf-8"))

                    attach = (
                        self.env["ir.attachment"]
                        .sudo()
                        .create(
                            {
                                "name": "missing_partners.csv",
                                "type": "binary",
                                "datas": payload,
                                "res_model": self._name,
                                "res_id": 0,
                                "mimetype": "text/csv",
                            }
                        )
                    )
                    if self.env.user.email:
                        self.env["mail.mail"].sudo().create(
                            {
                                "subject": _("Skipped rows on import for %s")
                                % (self._description or self._name),
                                "body_html": _(
                                    "<p>%s row(s) were skipped because partner was not found by VAT or Name.</p>"
                                )
                                % len(not_found),
                                "email_to": self.env.user.email,
                                "attachment_ids": [(6, 0, [attach.id])],
                            }
                        ).send()
                except Exception:
                    pass

        return super().load(fields, data)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to set employee_id."""
        records = super().create(vals_list)
        for record in records:
            record.employee_id = record._get_employee()
        return records

    # Business methods

    @api.model
    def _cron_create_reminder_activities(self):
        """Cron job to create reminder activities for upcoming queries."""
        days_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sarlaft_tracking.notification_days", default="30")
        )

        try:
            notification_days = int(days_param)
        except (ValueError, TypeError):
            notification_days = 30

        target_date = fields.Date.context_today(self) + timedelta(
            days=notification_days
        )
        records_to_notify = self.search(
            [
                ("next_query_date", "<=", target_date),
                ("activity_ids", "=", False),
            ]
        )
        sarlaft_group = self.env.ref(
            "sarlaft_tracking.group_sarlaft_admin", raise_if_not_found=False
        )
        if not sarlaft_group:
            return

        admin_users = sarlaft_group.users
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        if not activity_type:
            activity_type = self.env["mail.activity.type"].search(
                [("name", "=", "Todo")], limit=1
            )

        for record in records_to_notify:
            if record.employee_id and not record.employee_id.active:
                continue
            for user in admin_users:
                self.env["mail.activity"].create(
                    {
                        "activity_type_id": (
                            activity_type.id if activity_type else False
                        ),
                        "summary": f"SARLAFT Query Due for {record.display_name}",
                        "note": (
                            f"SARLAFT query is due on {record.next_query_date} for "
                            f"{record.display_name}. Risk level: {record.result_risks}"
                        ),
                        "date_deadline": record.next_query_date,
                        "user_id": user.id,
                        "res_model_id": self.env["ir.model"]
                        ._get("sarlaft.tracking")
                        .id,
                        "res_id": record.id,
                    }
                )
