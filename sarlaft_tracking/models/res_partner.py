# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    """Extend res.partner to add SARLAFT functionality."""

    _inherit = "res.partner"

    sarlaft_tracking_ids = fields.One2many(
        "sarlaft.tracking",
        "partner_id",
        string="SARLAFT Records",
        help="SARLAFT tracking records for this partner",
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
        for partner in self:
            partner.sarlaft_tracking_count = len(partner.sarlaft_tracking_ids)

    @api.depends(
        "sarlaft_tracking_ids.query_date",
        "sarlaft_tracking_ids.next_query_date",
        "sarlaft_tracking_ids.result_risk",
    )
    def _compute_last_sarlaft_data(self):
        """Compute last SARLAFT query data."""
        for partner in self:
            if partner.sarlaft_tracking_ids:
                latest_record = partner.sarlaft_tracking_ids.sorted(
                    "query_date", reverse=True
                )[0]
                partner.last_sarlaft_query_date = latest_record.query_date
                partner.next_sarlaft_query_date = latest_record.next_query_date
                partner.sarlaft_risk_level = latest_record.result_risk
            else:
                partner.last_sarlaft_query_date = False
                partner.next_sarlaft_query_date = False
                partner.sarlaft_risk_level = False

    def action_view_sarlaft_tracking(self):
        """Action to view SARLAFT tracking records for this partner."""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sarlaft_tracking.action_sarlaft_tracking"
        )

        if self.sarlaft_tracking_count == 1:
            action["views"] = [(False, "form")]
            action["res_id"] = self.sarlaft_tracking_ids[0].id
        else:
            action["domain"] = [("partner_id", "=", self.id)]
            action["context"] = {
                "default_partner_id": self.id,
            }

        return action
