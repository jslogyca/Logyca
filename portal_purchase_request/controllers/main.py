"""Controller for handling portal purchase requests."""

import base64
from collections import OrderedDict
from collections.abc import Iterable

from odoo import http
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.http import request
from odoo.tools.translate import _


class PortalPurchaseRequestController(http.Controller):

    @http.route(
        "/my/purchase_requests/<int:purchase_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_view_purchase_request_public(self, purchase_id, access_token=None, **kw):
        """Public portal view for a purchase request validated by access_token (read-only)."""
        if not access_token:
            return request.not_found()

        purchase_request = (
            request.env["portal.purchase.request"]
            .sudo()
            .search(
                [("id", "=", int(purchase_id)), ("access_token", "=", access_token)]
            )
        )

        if not purchase_request:
            return request.not_found()

        # compute display label for state (selection field) if possible
        state_display = None
        try:
            fld = purchase_request._fields.get("state")
            sel = getattr(fld, "selection", None)
            choices = None
            if callable(sel):
                try:
                    choices = sel(purchase_request)
                except TypeError:
                    try:
                        choices = sel(purchase_request.env)
                    except Exception:
                        choices = sel
            else:
                choices = sel
            if choices:
                if isinstance(choices, dict):
                    state_display = choices.get(purchase_request.state)
                else:
                    if isinstance(choices, Iterable):
                        iter_choices = list(choices)
                    else:
                        iter_choices = []
                    for item in iter_choices:
                        try:
                            k, v = item
                        except Exception:
                            continue
                        if k == purchase_request.state:
                            state_display = v
                            break
        except Exception:
            state_display = None

        # Prepare portal page values (chatter, history, etc.) using portal helpers
        values = {
            "purchase_request": purchase_request,
            "object": purchase_request,
            "state_display": state_display,
        }
        try:
            # Use portal._get_page_view_values to populate chatter-related vars
            portal_cls = portal.CustomerPortal
            get_vals = getattr(portal_cls, "_get_page_view_values")
            page_vals = get_vals(
                portal_cls,
                purchase_request,
                access_token,
                values,
                "my_purchase_requests",
                False,
            )
            # merge
            values.update(page_vals or {})
        except Exception:
            # fallback: render with basic values
            pass

        return request.render(
            "portal_purchase_request.portal_purchase_request_portal_view", values
        )

    @http.route("/purchase_request/view", type="http", auth="user")
    def view_purchase_request(self, access_token, id, **kwargs):
        """
        Route to view purchase request using access token.
        Redirects directly to the backend form view.
        Requires user authentication for security.
        """
        purchase_request = (
            request.env["portal.purchase.request"]
            .sudo()
            .search([("access_token", "=", access_token), ("id", "=", int(id))])
        )

        if not purchase_request:
            return request.not_found()

        return request.redirect(
            "/web#id=%s&model=portal.purchase.request&view_type=form" % id
        )

    @http.route(
        ["/purchase-request/new"],
        type="http",
        auth="public",
        methods=["GET", "POST"],
        website=True,
        csrf=False,
    )
    def public_purchase_request_form(self, **post):
        """
        Display and process the public purchase request form
        Allows unauthenticated users to submit purchase requests
        and handles form validation and file attachments
        """
        if request.httprequest.method == "POST":
            return self._process_public_form(post)

        companies = request.env["res.company"].sudo().search([])
        employees = request.env["hr.employee"].sudo().search([])
        jobs = request.env["hr.job"].sudo().search([])
        currencies = request.env["res.currency"].sudo().search([])
        budget_groups = request.env["logyca.budget_group"].sudo().search([])
        partners = request.env["res.partner"].sudo().search([("supplier_rank", ">", 0)])
        approvers = request.env["hr.employee"].sudo().search([])
        max_file_size = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("portal_purchase_request.max_file_size_mb", "10")
        )
        form_data = dict(post) if post else {}
        user_employee = (
            request.env.user.employee_ids and request.env.user.employee_ids[:1] or None
        )
        company = user_employee.company_id if user_employee else None
        currency = company.currency_id if company else None
        if not form_data.get("collaborator_id") and user_employee:
            form_data["collaborator_id"] = str(user_employee.id)
        if not form_data.get("division_id") and company:
            form_data["division_id"] = str(company.id)
        if not form_data.get("currency_id") and currency:
            form_data["currency_id"] = str(currency.id)

        analytic_accounts = request.env["account.analytic.account"].sudo().search([])
        analytic_accounts_map = {str(acc.id): acc.name for acc in analytic_accounts}

        values = {
            "companies": companies,
            "employees": employees,
            "jobs": jobs,
            "currencies": currencies,
            "budget_groups": budget_groups,
            "partners": partners,
            "approvers": approvers,
            "max_file_size": max_file_size,
            "analytic_accounts_map": analytic_accounts_map,
            "request_types": [
                ("asset_purchase", _("Asset Purchase")),
                ("service_request", _("Service Request")),
                ("quotation", _("Asset/Service Quotation")),
                ("policy", _("Policy Request")),
            ],
            "form_data": form_data,
            "errors": {},
        }

        return request.render(
            "portal_purchase_request.public_purchase_request_form", values
        )

    def _process_public_form(self, post):
        """Process the submitted public purchase request form"""
        errors = {}
        errors = self._validate_form_data(post)

        if errors:
            companies = request.env["res.company"].sudo().search([])
            employees = request.env["hr.employee"].sudo().search([])
            jobs = request.env["hr.job"].sudo().search([])
            currencies = request.env["res.currency"].sudo().search([])
            budget_groups = request.env["logyca.budget_group"].sudo().search([])
            partners = (
                request.env["res.partner"].sudo().search([("supplier_rank", ">", 0)])
            )
            approvers = request.env["hr.employee"].sudo().search([])
            max_file_size = int(
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("portal_purchase_request.max_file_size_mb", "10")
            )
            form_data = dict(post) if post else {}
            user_employee = (
                request.env.user.employee_ids
                and request.env.user.employee_ids[:1]
                or None
            )
            if not form_data.get("collaborator_id") and user_employee:
                form_data["collaborator_id"] = str(user_employee.id)

            values = {
                "companies": companies,
                "employees": employees,
                "jobs": jobs,
                "currencies": currencies,
                "budget_groups": budget_groups,
                "partners": partners,
                "approvers": approvers,
                "max_file_size": max_file_size,
                "request_types": [
                    ("asset_purchase", _("Asset Purchase")),
                    ("service_request", _("Service Request")),
                    ("quotation", _("Asset/Service Quotation")),
                    ("policy", _("Policy Request")),
                ],
                "form_data": form_data,
                "errors": errors,
            }

            return request.render(
                "portal_purchase_request.public_purchase_request_form", values
            )

        try:
            approver_ids = post.get("approver_ids")
            valid_approver_ids = []

            if approver_ids:
                if isinstance(approver_ids, str):
                    approver_ids = [
                        aid.strip() for aid in approver_ids.split(",") if aid.strip()
                    ]
                elif not isinstance(approver_ids, list):
                    approver_ids = []

                for aid in approver_ids:
                    try:
                        valid_approver_ids.append(int(aid))
                    except (ValueError, TypeError):
                        continue
            budget_group_id = (
                int(post.get("budget_group_id"))
                if post.get("budget_group_id")
                else False
            )
            analytic_distribution = ""
            if not analytic_distribution and budget_group_id:
                budget_group = (
                    request.env["logyca.budget_group"].sudo().browse(budget_group_id)
                )
                analytic_distribution = (
                    budget_group.analytic_distribution if budget_group else False
                )
            vals = {
                "collaborator_id": (
                    int(post.get("collaborator_id"))
                    if post.get("collaborator_id")
                    else False
                ),
                "division_id": (
                    int(post.get("division_id")) if post.get("division_id") else False
                ),
                "team_id": int(post.get("team_id")) if post.get("team_id") else False,
                "request_type": post.get("request_type"),
                "partner_id": (
                    int(post.get("partner_id")) if post.get("partner_id") else False
                ),
                "project_start_date": post.get("project_start_date") or False,
                "project_end_date": post.get("project_end_date") or False,
                "project_total_value": (
                    float(post.get("project_total_value", 0))
                    if post.get("project_total_value")
                    else 0.0
                ),
                "currency_id": (
                    int(post.get("currency_id")) if post.get("currency_id") else False
                ),
                "payment_agreement": post.get("payment_agreement") or False,
                "execution_place": post.get("execution_place") or False,
                "budget_group_id": budget_group_id or False,
                "analytic_distribution": analytic_distribution or "",
                "asset_responsible_id": (
                    int(post.get("asset_responsible_id"))
                    if post.get("asset_responsible_id")
                    else False
                ),
                "notes": post.get("notes") or False,
                "approve_ids": (
                    [(6, 0, valid_approver_ids)] if valid_approver_ids else False
                ),
            }

            purchase_request = (
                request.env["portal.purchase.request"].sudo().create(vals)
            )
            product_lines = []
            line_count = 0

            for key in post.keys():
                if key.startswith("product_description_"):
                    line_index = key.split("_")[-1]
                    if line_index.isdigit():
                        line_count = max(line_count, int(line_index) + 1)

            for i in range(line_count):
                description = post.get(f"product_description_{i}")
                quantity = post.get(f"product_quantity_{i}")

                if description and quantity:
                    try:
                        quantity_float = float(quantity)
                        if quantity_float > 0:
                            product_lines.append(
                                {
                                    "request_id": purchase_request.id,
                                    "description": description,
                                    "quantity": quantity_float,
                                }
                            )
                    except ValueError:
                        continue

            if product_lines:
                request.env["portal.purchase.request.line"].sudo().create(product_lines)

            self._process_attachments(request.httprequest.files, purchase_request)

            return request.render(
                "portal_purchase_request.public_purchase_request_success",
                {"purchase_request": purchase_request},
            )

        except Exception as e:
            purchase_request = locals().get("purchase_request")
            if purchase_request:
                try:
                    purchase_request.sudo().unlink()
                except:
                    pass

            errors["general"] = _("Error creating purchase request: %s") % str(e)

            companies = request.env["res.company"].sudo().search([])
            employees = request.env["hr.employee"].sudo().search([])
            jobs = request.env["hr.job"].sudo().search([])
            currencies = request.env["res.currency"].sudo().search([])
            budget_groups = request.env["logyca.budget_group"].sudo().search([])
            partners = (
                request.env["res.partner"].sudo().search([("supplier_rank", ">", 0)])
            )
            approvers = request.env["hr.employee"].sudo().search([])
            max_file_size = int(
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("portal_purchase_request.max_file_size_mb", "10")
            )

            values = {
                "companies": companies,
                "employees": employees,
                "jobs": jobs,
                "currencies": currencies,
                "budget_groups": budget_groups,
                "partners": partners,
                "approvers": approvers,
                "max_file_size": max_file_size,
                "request_types": [
                    ("asset_purchase", _("Asset Purchase")),
                    ("service_request", _("Service Request")),
                    ("quotation", _("Asset/Service Quotation")),
                    ("policy", _("Policy Request")),
                ],
                "form_data": post,
                "errors": errors,
            }

            return request.render(
                "portal_purchase_request.public_purchase_request_form", values
            )

    def _validate_form_data(self, post):
        """Validate form data and return errors dictionary"""
        errors = {}

        collaborator_id = post.get("collaborator_id")
        if not collaborator_id:
            errors["collaborator_id"] = _("Collaborator is required")
        if not post.get("division_id"):
            errors["division_id"] = _("Division is required")

        if not post.get("team_id"):
            errors["team_id"] = _("Team is required")

        if not post.get("budget_group_id"):
            errors["budget_group_id"] = _("Budget Group is required")

        if not post.get("request_type"):
            errors["request_type"] = _("Request type is required")

        start = post.get("project_start_date")
        end = post.get("project_end_date")
        if not start and not end:
            errors["project_start_date"] = _("Project dates are required")
        else:
            if not start:
                errors["project_start_date"] = _("Project start date is required")
            if not end:
                errors["project_end_date"] = _("Project end date is required")

        if start and end:
            try:
                from datetime import datetime

                start_date = datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.strptime(end, "%Y-%m-%d")
                if start_date > end_date:
                    errors["project_end_date"] = _(
                        "Project start date must be before the end date."
                    )
            except ValueError:
                errors["project_dates"] = _("Invalid date format")

        if not post.get("execution_place"):
            errors["execution_place"] = _("Execution place is required")

        project_total_value = post.get("project_total_value")
        currency_id = post.get("currency_id")
        if not project_total_value and not currency_id:
            errors["project_total_value"] = _(
                "Project total value and currency are required"
            )
        else:
            if not project_total_value:
                errors["project_total_value"] = _("Project total value is required")
            if not currency_id:
                errors["currency_id"] = _("Currency is required")
            try:
                value = float(project_total_value)
                if value <= 0:
                    errors["project_total_value"] = _(
                        "Project total value must be positive and greater than zero."
                    )
            except ValueError:
                errors["project_total_value"] = _("Invalid numeric value")

        if not post.get("payment_agreement"):
            errors["payment_agreement"] = _("Payment agreement is required")

        has_product_line = False
        line_count = 0
        for key in post.keys():
            if key.startswith("product_description_"):
                line_index = key.split("_")[-1]
                if line_index.isdigit():
                    line_count = max(line_count, int(line_index) + 1)

        for i in range(line_count):
            description = post.get(f"product_description_{i}")
            quantity = post.get(f"product_quantity_{i}")

            if description and description.strip():
                has_product_line = True
                if quantity:
                    try:
                        qty = float(quantity)
                        if qty <= 0:
                            errors[f"product_quantity_{i}"] = _(
                                "Quantity must be greater than zero"
                            )
                    except ValueError:
                        errors[f"product_quantity_{i}"] = _("Invalid quantity")
                else:
                    errors[f"product_quantity_{i}"] = _(
                        "Quantity is required when description is provided"
                    )

        if not has_product_line:
            errors["product_lines"] = _("At least one product line is required")

        approver_ids = post.get("approver_ids")
        if not approver_ids:
            errors["approver_ids"] = _("At least one approver is required")
        else:
            if isinstance(approver_ids, str):
                approver_ids = [
                    aid.strip() for aid in approver_ids.split(",") if aid.strip()
                ]
            elif not isinstance(approver_ids, list):
                approver_ids = []

            if not approver_ids or not any(approver_ids):
                errors["approver_ids"] = _("Please select at least one approver")

            if collaborator_id in approver_ids:
                errors["approver_ids"] = _(
                    "Collaborator cannot be one of the approvers."
                )

        max_file_size_mb = int(
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("portal_purchase_request.max_file_size_mb", "10")
        )
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        total_size = 0
        files_present = False

        if hasattr(request.httprequest, "files"):
            for file_field_name, file_data in request.httprequest.files.items():
                entries = (
                    file_data if isinstance(file_data, (list, tuple)) else [file_data]
                )
                for fd in entries:
                    filename = getattr(fd, "filename", None)
                    stream = getattr(fd, "stream", None)
                    file_size = 0
                    if filename and stream is not None:
                        current_pos = None
                        try:
                            current_pos = stream.tell()
                        except Exception:
                            current_pos = None
                        try:
                            stream.seek(0, 2)
                            file_size = stream.tell()
                            if current_pos is not None:
                                stream.seek(current_pos)
                            else:
                                stream.seek(0)
                        except Exception:
                            try:
                                if not isinstance(fd, (bytes, bytearray)) and hasattr(
                                    fd, "read"
                                ):
                                    content = fd.read()
                                    if content:
                                        file_size = len(content)

                                if not isinstance(fd, (bytes, bytearray)) and hasattr(
                                    fd, "seek"
                                ):
                                    try:
                                        fd.seek(0)
                                    except Exception:
                                        pass
                            except Exception:
                                file_size = 0
                    elif filename:
                        try:
                            if not isinstance(fd, (bytes, bytearray)) and hasattr(
                                fd, "read"
                            ):
                                content = fd.read()
                                if content:
                                    file_size = len(content)
                            if not isinstance(fd, (bytes, bytearray)) and hasattr(
                                fd, "seek"
                            ):
                                try:
                                    fd.seek(0)
                                except Exception:
                                    pass
                        except Exception:
                            file_size = 0

                    if file_size > 0:
                        files_present = True
                        total_size += file_size

        if not files_present:
            errors["attachments"] = _("At least one attachment is required")
        elif total_size > max_file_size_bytes:
            errors["attachments"] = (
                _("Total file size exceeds maximum allowed size of %s MB")
                % max_file_size_mb
            )

        return errors

    def _process_attachments(self, files, purchase_request):
        """Process and save file attachments to the purchase request"""
        if not files:
            return

        for file_field_name, file_data in files.items():
            if hasattr(file_data, "read") and file_data.filename:
                file_content = file_data.read()
                if file_content:
                    attachment_vals = {
                        "name": file_data.filename,
                        "datas": base64.b64encode(file_content),
                        "res_model": "portal.purchase.request",
                        "res_id": purchase_request.id,
                        "public": False,
                    }
                    request.env["ir.attachment"].sudo().create(attachment_vals)


class PortalPurchaseRequestPortal(portal.CustomerPortal):
    """Extend portal home values to include purchase_request_count for portal dashboard cards"""

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        PurchaseRequest = request.env["portal.purchase.request"]
        if "purchase_request_count" in counters:
            if PurchaseRequest.has_access("read"):
                user_emp = (
                    request.env.user.employee_ids
                    and request.env.user.employee_ids[0]
                    or None
                )
                if user_emp:
                    values["purchase_request_count"] = PurchaseRequest.search_count(
                        [("collaborator_id", "=", user_emp.id)]
                    )
                else:
                    values["purchase_request_count"] = 0
            else:
                values["purchase_request_count"] = 0
        return values

    def _get_purchase_request_searchbar_sortings(self):
        return {
            "date": {"label": _("Newest"), "order": "create_date desc, id desc"},
            "name": {"label": _("Name"), "order": "name asc, id asc"},
        }

    def _render_portal(
        self,
        template,
        page,
        date_begin,
        date_end,
        sortby,
        filterby,
        domain,
        searchbar_filters,
        default_filter,
        url,
        history,
        page_name,
        key,
    ):
        """Render a portal listing for portal.purchase.request mirroring purchase._render_portal.

        Inputs:
        - template: xml id to render
        - page: current page (int)
        - date_begin/date_end: optional date filters
        - sortby/filterby: sorting/filter keys
        - domain: base domain list
        - searchbar_filters: dict of filters {key: {'label':..., 'domain': [...]}}
        - default_filter: default filter key
        - url: base url for pager
        - history: session key to store last ids
        - page_name: page name for templates
        - key: variable name to inject in values (usually 'requests')

        Outputs: returns request.render(template, values) where values contains:
        - portal layout values from self._prepare_portal_layout_values()
        - date, key (recordset), page_name, pager (dict), searchbar_sortings (dict), sortby, searchbar_filters (OrderedDict), filterby, default_url
        Types: key is a recordset of model 'portal.purchase.request'; pager is a dict; searchbar_filters is OrderedDict.
        """
        values = self._prepare_portal_layout_values()
        PurchaseRequest = request.env["portal.purchase.request"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        searchbar_sortings = self._get_purchase_request_searchbar_sortings()
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if searchbar_filters:
            if not filterby:
                filterby = default_filter
            domain += searchbar_filters[filterby]["domain"]

        count = PurchaseRequest.search_count(domain)

        pager = portal_pager(
            url=url,
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
            },
            total=count,
            page=page,
            step=self._items_per_page,
        )

        recs = PurchaseRequest.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )
        request.session[history] = recs.ids[:100]

        values.update(
            {
                "date": date_begin,
                key: recs,
                "page_name": page_name,
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "searchbar_filters": (
                    OrderedDict(sorted(searchbar_filters.items()))
                    if searchbar_filters
                    else OrderedDict()
                ),
                "filterby": filterby,
                "default_url": url,
            }
        )
        return request.render(template, values)

    @http.route(
        ["/my/purchase_requests", "/my/purchase_requests/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_requests(self, page=1, **kw):
        # prepare domain based on the employee linked to the current user
        user_emp = (
            request.env.user.employee_ids and request.env.user.employee_ids[:1] or None
        )
        if user_emp:
            domain = [("collaborator_id", "=", user_emp.id)]
        else:
            domain = [("collaborator_id", "=", False)]

        # Use the shared _render_portal implementation to provide paged recordset and layout values
        return self._render_portal(
            "portal_purchase_request.portal_purchase_request_list",
            page,
            None,
            None,
            None,
            None,
            domain,
            {},
            None,
            "/my/purchase_requests",
            "my_purchase_requests_history",
            "purchase_requests",
            "requests",
        )
