# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrEmployee(models.Model):
    """Extend hr.employee to add SARLAFT functionality."""

    _inherit = "hr.employee"

    sarlaft_tracking_ids = fields.One2many(
        "sarlaft.tracking",
        "employee_id",
        string="SARLAFT Records",
        help="SARLAFT tracking records for this employee",
    )
    sarlaft_tracking_count = fields.Integer(
        string="SARLAFT Records Count", compute="_compute_sarlaft_tracking_count"
    )
    last_sarlaft_query_date = fields.Date(
        string="Last SARLAFT Query",
        compute="_compute_last_sarlaft_data",
        store=True,
        help="Date of the last SARLAFT query",
    )
    next_sarlaft_query_date = fields.Date(
        string="Next SARLAFT Query",
        compute="_compute_last_sarlaft_data",
        store=True,
        help="Date of the next SARLAFT query",
    )
    sarlaft_risk_level = fields.Selection(
        [
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
        ],
        string="SARLAFT Risk Level",
        compute="_compute_last_sarlaft_data",
        store=True,
        help="Latest SARLAFT risk level",
    )

    @api.depends("sarlaft_tracking_ids")
    def _compute_sarlaft_tracking_count(self):
        """Compute the count of SARLAFT tracking records."""
        for employee in self:
            employee.sarlaft_tracking_count = len(employee.sarlaft_tracking_ids)

    @api.depends(
        "sarlaft_tracking_ids.query_date",
        "sarlaft_tracking_ids.next_query_date",
        "sarlaft_tracking_ids.result_risk",
    )
    def _compute_last_sarlaft_data(self):
        """Compute last SARLAFT query data."""
        for employee in self:
            if employee.sarlaft_tracking_ids:
                latest_record = employee.sarlaft_tracking_ids.sorted(
                    "query_date", reverse=True
                )[0]
                employee.last_sarlaft_query_date = latest_record.query_date
                employee.next_sarlaft_query_date = latest_record.next_query_date
                employee.sarlaft_risk_level = latest_record.result_risk
            else:
                employee.last_sarlaft_query_date = False
                employee.next_sarlaft_query_date = False
                employee.sarlaft_risk_level = False

    def action_view_sarlaft_tracking(self):
        """Action to view SARLAFT tracking records for this employee."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sarlaft_tracking.action_sarlaft_tracking"
        )

        if self.sarlaft_tracking_count == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = self.sarlaft_tracking_ids[0].id
        else:
            action["domain"] = [("employee_id", "=", self.id)]
            action["context"] = {
                "default_employee_id": self.id,
            }

        return action
