# -*- coding: utf-8 -*-

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
        required=True,
        help="Date for the next SARLAFT query",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        help="Company that performed the query",
    )
    requested_by = fields.Char(
        string="Requested By",
        required=True,
        tracking=True,
        help="User who requested the SARLAFT query",
    )
    registration_number = fields.Integer(
        string="Registration Number",
        required=True,
        help="Sequential registration number",
    )
    # Identification fields
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
        readonly=True,
        help="Identification document number",
    )
    # Query information
    result_option = fields.Many2one(
        "sarlaft.option",
        string="Result Option",
        required=True,
        tracking=True,
        help="Option selected for the SARLAFT query result",
    )
    result_risk = fields.Selection(
        [
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ],
        string="Risk Level",
        required=True,
        tracking=True,
        help="Risk level determined from the query",
    )
    information = fields.Text(
        string="Additional Information",
        required=True,
        help="Additional information about the query",
    )
    result_link = fields.Char(
        string="Result Link",
        required=True,
        help="URL link to the detailed query result",
    )
    comments = fields.Text(
        string="Comments",
        help="Additional comments about the query",
    )
    partner_type = fields.Selection(
        [
            ("customer", "Customer"),
            ("supplier", "Supplier"),
            ("employee", "Employee"),
        ],
        string="Partner Type",
        required=True,
        tracking=True,
        help="Type of third party",
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

    @api.depends("partner_id", "employee_id", "registration_number", "partner_type")
    def _compute_display_name(self):
        """Compute display name based on partner/employee and registration number."""
        for record in self:
            if record.partner_type == "employee" and record.employee_id:
                name = record.employee_id.name
            elif record.partner_id:
                name = record.partner_id.name
            else:
                name = record.ident_number or "Unknown"

            if record.registration_number:
                record.display_name = f"[{record.registration_number}] {name}"
            else:
                record.display_name = name

    @api.depends("next_query_date")
    def _compute_is_overdue(self):
        """Compute if the record is overdue for next query."""
        today = fields.Date.context_today(self)
        for record in self:
            record.is_overdue = (
                record.next_query_date and record.next_query_date < today
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

    def _get_employee(self):
        """Get the employee associated with the current record."""
        self.ensure_one()
        employee = False
        if self.partner_id and self.partner_id.employee_ids:
            employee = self.partner_id.employee_ids[0]
        return employee

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Update employee_id based on selected partner."""
        for record in self:
            record.employee_id = record._get_employee()

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

    def name_get(self):
        """Return a more descriptive name for the record."""
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create method to set employee_id."""
        records = super().create(vals_list)
        for record in records:
            record.employee_id = record._get_employee()
        return records

    @api.model
    def _cron_create_reminder_activities(self):
        """Cron job to create reminder activities for upcoming queries."""
        # Get the notification days parameter
        days_param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sarlaft_tracking.notification_days", default="30")
        )

        try:
            notification_days = int(days_param)
        except (ValueError, TypeError):
            notification_days = 30

        # Calculate the target date
        target_date = fields.Date.context_today(self) + timedelta(
            days=notification_days
        )

        # Find records that need notification
        records_to_notify = self.search(
            [
                ("next_query_date", "<=", target_date),
                ("activity_ids", "=", False),  # No existing activities
            ]
        )

        # Get SARLAFT Administration group users
        sarlaft_group = self.env.ref(
            "sarlaft_tracking.group_sarlaft_admin", raise_if_not_found=False
        )
        if not sarlaft_group:
            return

        admin_users = sarlaft_group.users

        # Create activities for each record and each admin user
        activity_type = self.env.ref(
            "mail.mail_activity_data_todo", raise_if_not_found=False
        )
        if not activity_type:
            activity_type = self.env["mail.activity.type"].search(
                [("name", "=", "Todo")], limit=1
            )

        for record in records_to_notify:
            for user in admin_users:
                risk_level = dict(record._fields["result_risk"].selection).get(
                    record.result_risk, "Not defined"
                )

                self.env["mail.activity"].create(
                    {
                        "activity_type_id": (
                            activity_type.id if activity_type else False
                        ),
                        "summary": f"SARLAFT Query Due for {record.display_name}",
                        "note": (
                            f"SARLAFT query is due on {record.next_query_date} for "
                            f"{record.display_name}. Risk level: {risk_level}"
                        ),
                        "date_deadline": record.next_query_date,
                        "user_id": user.id,
                        "res_model_id": self.env["ir.model"]
                        ._get("sarlaft.tracking")
                        .id,
                        "res_id": record.id,
                    }
                )


class SarlaftOption(models.Model):
    _name = "sarlaft.option"
    _description = "SARLAFT Query Result Option"

    name = fields.Char(string="Option Name", required=True)
    description = fields.Text(string="Option Description")
    active = fields.Boolean(string="Active", default=True)
