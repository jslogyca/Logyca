"""Portal Purchase Request Model"""

import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PortalPurchaseRequest(models.Model):
    _name = "portal.purchase.request"
    _description = "Portal Purchase Request"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "analytic.mixin"]
    _order = "id desc"

    name = fields.Char(string="Reference", readonly=True)
    access_token = fields.Char(string="Access Token", copy=False, readonly=True)
    collaborator_id = fields.Many2one("hr.employee", string="Collaborator")
    division_id = fields.Many2one(
        "res.company",
        string="Company name",
        help="Company name of the company through which the service/purchase is performed.",
    )
    team_id = fields.Many2one("hr.job", string="Team")
    request_date = fields.Date(string="Request Date", default=fields.Date.context_today)
    request_type = fields.Selection(
        [
            ("asset_purchase", "Asset Purchase"),
            ("service_request", "Service Request"),
            ("quotation", "Asset/Service Quotation"),
            ("policy", "Policy Request"),
        ],
        string="Request Type",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    partner_id = fields.Many2one("res.partner", string="Vendor")
    product_line_ids = fields.One2many(
        "portal.purchase.request.line", "request_id", string="Products"
    )
    project_start_date = fields.Date(string="Project Start Date")
    project_end_date = fields.Date(string="Project End Date")
    project_total_value = fields.Monetary(string="Project Total Value")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    payment_agreement = fields.Char(string="Payment Agreement")
    execution_place = fields.Char(string="Execution Place")
    budget_group_id = fields.Many2one("logyca.budget_group", string="Budget Group")
    asset_responsible_id = fields.Many2one("hr.employee", string="Asset Responsible")
    notes = fields.Text(string="Notes")
    approve_ids = fields.Many2many("hr.employee", string="Approvers", readonly=True)
    reviewed_by_id = fields.Many2one("hr.employee", string="Reviewed By", readonly=True)
    purchase_order_count = fields.Integer(
        string="Purchase Orders Count", compute="_compute_purchase_order_count"
    )
    purchase_order_ids = fields.Many2many(
        "purchase.order",
        string="Purchase Orders",
        compute="_compute_purchase_order_count",
    )
    completion_date = fields.Date(
        string="Completion Date",
        readonly=True,
    )
    reason = fields.Char(string="Reason", tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_process", "In Process"),
            ("to_invoice", "To Invoice"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("completed", "Completed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Constraints functions

    @api.constrains(
        "collaborator_id",
        "approve_ids",
    )
    def _check_approvers(self):
        """Ensure collaborator is not in approvers and at least one approver exists"""
        for rec in self:
            if rec.collaborator_id and rec.collaborator_id in rec.approve_ids:
                raise ValidationError(_("Collaborator cannot be one of the approvers."))
            if not rec.approve_ids:
                raise ValidationError(
                    _("At least one leader must approve the request.")
                )

    @api.constrains("project_start_date", "project_end_date")
    def _check_project_dates(self):
        """Ensure start date is before end date"""
        for rec in self:
            if (
                rec.project_start_date
                and rec.project_end_date
                and rec.project_start_date > rec.project_end_date
            ):
                raise ValidationError(
                    _("Project start date must be before the end date.")
                )

    @api.constrains("project_total_value")
    def _check_project_total_value(self):
        """Ensure project total value is positive and greater than zero"""
        for rec in self:
            if rec.project_total_value <= 0:
                raise ValidationError(
                    _("Project total value must be positive and greater than zero.")
                )

    # Auxiliary functions

    def _get_collaborator(self, collaborator=False):
        employee = collaborator

        if not employee:
            employees = self.env.user.employee_ids
            employee = employees[0] if employees else False

        vals = {
            "employee": False,
            "job": False,
            "division": False,
        }

        if employee and hasattr(employee, "id"):
            employee_id = getattr(employee, "id", False)
            job_id = getattr(employee, "job_id", False)
            company_id = getattr(employee, "company_id", False)

            vals.update(
                {
                    "employee": employee_id,
                    "job": getattr(job_id, "id", False) if job_id else False,
                    "division": (
                        getattr(company_id, "id", False) if company_id else False
                    ),
                }
            )

        return vals

    def _get_allowed_option(self):
        """Check if the current user is allowed to approve or reject the request"""
        self.ensure_one()
        not_allowed = _("You are not authorized to reject this request")
        user_emp = self.env.user.employee_ids and self.env.user.employee_ids[0]
        allowed = user_emp and user_emp.id in self.approve_ids.ids
        return False if allowed else not_allowed

    def _show_error_msg(self, errors):
        """Show error message if there are any errors"""
        if errors:
            error_msg = _("Please fix the following errors:\n\n") + "\n".join(errors)
            raise ValidationError(error_msg)

    def _send_message_post(self, msg_type):
        """Post a message in the chatter and send notifications based on the message type"""
        self.ensure_one()
        if msg_type == "new":
            body = _("New purchase request created: %s") % (self.name)
        elif msg_type == "approve":
            body = _("Request approved: %s") % self.name
            self._send_manager_notification()
        elif msg_type == "reject":
            body = _("Request rejected: %s - %s") % (self.name, self.reason)
        elif msg_type == "cancel":
            body = _("Request cancelled: %s - %s") % (self.name, self.reason)
        else:
            return False

        self.message_post(body=body)
        self._send_state_change_notification()

    def _send_manager_notification(self):
        """Send email notification to all users in the group_purchase_request_manager group"""
        self.ensure_one()
        group = self.env.ref("portal_purchase_request.group_purchase_request_manager")
        managers = group.users.mapped("partner_id")
        template = self.env.ref(
            "portal_purchase_request.email_template_purchase_request_manager_notification"
        )
        if managers and template:
            for manager in managers:
                template.with_context(
                    email_to=manager.email, recipient_ids=[(4, manager.id)]
                ).send_mail(
                    self.id,
                    force_send=False,
                    email_layout_xmlid="mail.mail_notification_light",
                )

        return True

    def _send_state_change_notification(self):
        """Send email notification to the collaborator about the state change"""
        self.ensure_one()
        template = self.env.ref(
            "portal_purchase_request.email_template_purchase_request_state_change"
        )
        if template and self.collaborator_id and self.collaborator_id.work_email:
            template.with_context(
                email_to=self.collaborator_id.work_email,
            ).send_mail(
                self.id,
                force_send=False,
                email_layout_xmlid="mail.mail_notification_light",
            )
        return True

    def _get_purchase_orders(self):
        """Get all purchase orders related to this request"""
        self.ensure_one()
        purchase_orders = self.env["purchase.order"].search(
            [("portal_request_id", "=", self.id)]
        )

        return purchase_orders

    def _reset_approval_datas(self):
        """Reset approval related fields"""
        self.ensure_one()
        self.completion_date = False
        self.reviewed_by_id = False

    # Compute and onchange functions

    @api.depends("name")
    def _compute_purchase_order_count(self):
        """Compute the count of purchase orders related to this request"""
        for record in self:
            record.purchase_order_ids = record._get_purchase_orders()
            record.purchase_order_count = len(record.purchase_order_ids)

    @api.onchange("collaborator_id")
    def _onchange_collaborator(self):
        """Update team and division based on selected collaborator"""
        for rec in self:
            if rec.collaborator_id:
                employee_vals = self._get_collaborator(rec.collaborator_id)
                rec.team_id = employee_vals.get("job")
                rec.division_id = employee_vals.get("division")

    @api.onchange("budget_group_id")
    def _onchange_budget_group(self):
        """Update analytic distribution based on selected budget group"""
        for rec in self:
            if rec.budget_group_id:
                rec.analytic_distribution = rec.budget_group_id.analytic_distribution
            else:
                rec.analytic_distribution = False

    # Inherit base methods

    def default_get(self, fields_list):
        """Inherit default_get to set default collaborator, team, and division"""
        res = super().default_get(fields_list)
        if "collaborator_id" in fields_list and not res.get("collaborator_id"):
            employee_vals = self._get_collaborator()
            res["collaborator_id"] = employee_vals.get("employee")
            res["team_id"] = employee_vals.get("job")
            res["division_id"] = employee_vals.get("division")

        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Inherit create to set name, access token, default collaborator, and division"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("portal.purchase.request")
                    or "/"
                )
            # Generate access token
            if not vals.get("access_token"):
                vals["access_token"] = str(uuid.uuid4())
            # default collaborator from user
            if not vals.get("collaborator_id"):
                employee = (
                    self.env.user.employee_ids and self.env.user.employee_ids[0] or None
                )
                if employee:
                    vals["collaborator_id"] = employee.id
            if not vals.get("division_id"):
                vals["division_id"] = self.env.company.id
        res = super().create(vals_list)
        for rec in res:
            rec._send_message_post("new")
        return res

    def write(self, vals):
        """Inherit write to restrict modifications based on state"""
        for rec in self:
            permit_values = ["reason", "completion_date", "reviewed_by_id"]
            if "state" in vals and vals["state"] in ["cancelled", "rejected", "draft"]:
                continue
            elif rec.state not in ["draft", "in_process", "to_invoice"]:
                if any(key in permit_values for key in vals.keys()):
                    continue
                raise UserError(
                    _(
                        "You cannot modify a purchase request that is not in draft, in process, or to invoice state."
                    )
                )
        return super().write(vals)

    def action_view_purchase_orders(self):
        """Open related purchase orders in form or list view"""
        self.ensure_one()
        purchase_orders = self._get_purchase_orders()

        if len(purchase_orders) == 1:
            return {
                "type": "ir.actions.act_window",
                "name": _("Purchase Order"),
                "res_model": "purchase.order",
                "res_id": purchase_orders.id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            return {
                "type": "ir.actions.act_window",
                "name": _("Purchase Orders"),
                "res_model": "purchase.order",
                "view_mode": "list,form",
                "domain": [("portal_request_id", "=", self.id)],
                "target": "current",
            }

    def action_create_purchase_order(self):
        """Open wizard to create a purchase order from this request"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Purchase Order"),
            "res_model": "purchase.order.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "active_id": self.id,
                "default_purchase_request_id": self.id,
                "default_currency_id": self.currency_id.id
                or self.env.company.currency_id.id,
                "default_partner_id": self.partner_id.id or False,
                "default_budget_group_id": self.budget_group_id.id or False,
                "default_analytic_distribution": self.analytic_distribution or False,
            },
        }

    # Business logic functions

    def action_approve(self):
        """Approve the purchase request if the user is authorized and validations pass"""
        for rec in self:
            error_list = []
            not_allowed = rec._get_allowed_option()
            if not_allowed:
                error_list.append(not_allowed)

            if not rec.product_line_ids:
                error_list.append(
                    _("You must add at least one product line to approve the request")
                )

            rec._show_error_msg(error_list)
            rec.state = "in_process"
            rec.reviewed_by_id = (
                self.env.user.employee_ids and self.env.user.employee_ids[0].id or False
            )
            rec._send_message_post("approve")

    def action_reject(self):
        """Reject the purchase request if the user is authorized and validations pass"""
        for rec in self:
            error_list = []
            not_allowed = rec._get_allowed_option()
            if not_allowed:
                error_list.append(not_allowed)

            if not rec.reason:
                error_list.append(_("You must provide a reason for rejection"))

            rec._show_error_msg(error_list)
            rec.state = "rejected"
            rec._send_message_post("reject")
            rec._reset_approval_datas()

    def action_cancel(self):
        """Cancel the purchase request and related purchase orders if validations pass"""
        for rec in self:
            error_list = []
            purchase_orders = self._get_purchase_orders()

            if any(
                purchase_order.state in ("purchase", "done")
                for purchase_order in purchase_orders
            ):
                error_list.append(
                    _("You cannot cancel a confirmed purchase order: %s")
                    % ", ".join(
                        purchase_order.name for purchase_order in purchase_orders
                    )
                )
            else:
                for purchase_order in purchase_orders:
                    if purchase_order.state != "cancel":
                        purchase_order.button_cancel()

            if not rec.reason:
                error_list.append(_("You must provide a reason for cancellation"))

            rec._show_error_msg(error_list)
            rec.state = "cancelled"
            rec._send_message_post("cancel")
            rec._reset_approval_datas()

    def action_to_draft(self):
        """Reset the purchase request to draft state if it is currently cancelled"""
        for rec in self:
            error_list = []

            if rec.state != "cancelled":
                error_list.append(_("Only cancelled requests can be set to draft"))

            rec._show_error_msg(error_list)
            rec.state = "draft"
            rec._send_message_post("to_draft")
            rec._reset_approval_datas()
