# See LICENSE file for full copyright and licensing details.

import json
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

URL = "webservice.php"


class ResCompany(models.Model):
    _inherit = "res.company"

    access_key = fields.Char()
    vtiger_server = fields.Char()
    user_name = fields.Char()
    last_sync_date = fields.Datetime(string="Last Synced Time")
    vtiger_progress_from_date = fields.Datetime(string="Progress From Date")
    last_vtiger_progress_check = fields.Datetime(string="Last Progress Check")
    vtiger_partner_progress = fields.Float(string="Partners", readonly=True)
    vtiger_product_progress = fields.Float(string="Products", readonly=True)
    vtiger_pricebook_progress = fields.Float(string="Price Books", readonly=True)
    vtiger_crm_progress = fields.Float(string="CRM", readonly=True)
    vtiger_sale_progress = fields.Float(string="Sale Orders", readonly=True)
    vtiger_purchase_progress = fields.Float(string="Purchase Orders", readonly=True)
    vtiger_invoice_progress = fields.Float(string="Invoices", readonly=True)
    vtiger_calendar_progress = fields.Float(string="Calendar Events", readonly=True)
    vtiger_project_progress = fields.Float(string="Projects / Tasks", readonly=True)
    vtiger_helpdesk_progress = fields.Float(string="HelpDesk", readonly=True)
    has_vtiger_master_connector = fields.Boolean(
        compute="_compute_vtiger_connector_sections"
    )
    has_vtiger_transactional_connector = fields.Boolean(
        compute="_compute_vtiger_connector_sections"
    )
    has_vtiger_connector = fields.Boolean(compute="_compute_vtiger_connector_sections")

    def _compute_vtiger_connector_sections(self):
        installed_modules = set(
            self.env["ir.module.module"]
            .sudo()
            .search([("state", "=", "installed")])
            .mapped("name")
        )
        master_modules = {
            "vtiger_connector_partner",
            "vtiger_connector_products",
            "vtiger_connector_pricebook",
        }
        transactional_modules = {
            "vtiger_connector_calendar",
            "vtiger_connector_crm",
            "vtiger_connector_helpdesk",
            "vtiger_connector_invoice",
            "vtiger_connector_project",
            "vtiger_connector_purchase",
            "vtiger_connector_sales",
        }
        has_master_connector = bool(master_modules.intersection(installed_modules))
        has_transactional_connector = bool(
            transactional_modules.intersection(installed_modules)
        )
        for company in self:
            company.has_vtiger_master_connector = has_master_connector
            company.has_vtiger_transactional_connector = has_transactional_connector
            company.has_vtiger_connector = (
                has_master_connector or has_transactional_connector
            )

    def _check_vtiger_connection_config(self):
        for company in self:
            missing_fields = []
            if not company.vtiger_server:
                missing_fields.append(_("VTiger Server"))
            if not company.user_name:
                missing_fields.append(_("User Name"))
            if not company.access_key:
                missing_fields.append(_("Access Key"))
            if missing_fields:
                raise UserError(
                    _(
                        "Please configure the following VTiger details before syncing: %s"
                    )
                    % ", ".join(missing_fields)
                )

    def get_vtiger_server_url(self):
        return "%s/%s" % (self.vtiger_server, URL)

    def get_vtiger_access_key(self):
        """Get the token using 'getchallenge' operation"""
        self.ensure_one()
        self._check_vtiger_connection_config()
        values = {"operation": "getchallenge", "username": self.user_name}
        data = urlencode(values)
        url = self.get_vtiger_server_url()
        req = urlopen("%s?%s" % (url, data), timeout=20)
        response = req.read()
        token = json.loads(response)["result"]["token"]
        # Use the TOKEN + ACCESSKEY to create the tokenized accessKey
        tokenized_accessKey = md5(
            token.encode("utf-8") + self.access_key.encode("utf-8")
        )
        return tokenized_accessKey.hexdigest()

    def vtiger_login(self, access_key):
        """Using AccessKey tokenized, perform a login operation."""
        self.ensure_one()
        self._check_vtiger_connection_config()
        values = {
            "operation": "login",
            "username": self.user_name,
            "accessKey": access_key,
        }
        url = self.get_vtiger_server_url()
        response = requests.post(url=url, data=values, timeout=20).json()
        # Return sessionName
        return response["result"]["sessionName"]

    @api.model
    def sync_vtiger(self):
        return self.search(
            [
                "&",
                ("user_name", "!=", False),
                ("access_key", "!=", False),
                ("vtiger_server", "!=", False),
            ]
        ).action_sync_vtiger_all()

    def action_sync_vtiger_master_data(self):
        for company in self:
            if hasattr(company, "sync_vtiger_partner"):
                company.sync_vtiger_partner()
            if hasattr(company, "sync_vtiger_service_products"):
                company.sync_vtiger_service_products()
            if hasattr(company, "sync_vtiger_pricebook"):
                company.sync_vtiger_pricebook()
        return True

    def action_sync_vtiger_transactional_data(self):
        for company in self:
            if hasattr(company, "sync_vtiger_crm"):
                company.sync_vtiger_crm()
            if hasattr(company, "sync_vtiger_sale_order"):
                company.sync_vtiger_sale_order()
            if hasattr(company, "sync_vtiger_purchase_order"):
                company.sync_vtiger_purchase_order(full_sync=True)
            if hasattr(company, "sync_vtiger_invoice"):
                company.sync_vtiger_invoice(full_sync=True)
            if hasattr(company, "sync_vtiger_calendar_event"):
                company.sync_vtiger_calendar_event(full_sync=True)
            if hasattr(company, "sync_vtiger_project_task"):
                company.sync_vtiger_project_task()
            if hasattr(company, "sync_vtiger_helpdesk_ticket"):
                company.sync_vtiger_helpdesk_ticket(full_sync=True)
            if hasattr(company, "sync_vtiger_document"):
                company.sync_vtiger_document()
        return True

    def action_sync_vtiger_all(self):
        self.action_sync_vtiger_master_data()
        self.action_sync_vtiger_transactional_data()
        self.write({"last_sync_date": datetime.now()})
        return True

    def action_sync_vtiger(self):
        # TODO: If we need multi-company, here we have to update code.
        self.write({"last_sync_date": datetime.now()})
        return True

    def _vtiger_progress_definitions(self):
        return {
            "vtiger_partner_progress": {
                "modules": ("Contacts", "Vendors", "Accounts"),
                "model": "res.partner",
            },
            "vtiger_product_progress": {
                "modules": ("Products", "Services"),
                "model": "product.template",
            },
            "vtiger_pricebook_progress": {
                "modules": ("PriceBooks",),
                "model": "product.pricelist",
            },
            "vtiger_crm_progress": {
                "modules": ("Leads", "Potentials"),
                "model": "crm.lead",
            },
            "vtiger_sale_progress": {
                "modules": ("SalesOrder", "Quotes"),
                "model": "sale.order",
            },
            "vtiger_purchase_progress": {
                "modules": ("PurchaseOrder",),
                "model": "purchase.order",
            },
            "vtiger_invoice_progress": {
                "modules": ("Invoice",),
                "model": "account.move",
            },
            "vtiger_calendar_progress": {
                "modules": ("Events",),
                "model": "calendar.event",
            },
            "vtiger_project_progress": {
                "modules": ("Project", "ProjectTask"),
                "models": ("project.project", "project.task"),
            },
            "vtiger_helpdesk_progress": {
                "modules": ("HelpDesk", "ServiceContracts"),
                "model": "helpdesk.ticket",
                "id_format": "%(module)s:%s",
            },
        }

    def _execute_vtiger_count_query(self, vtiger_module, session_name):
        qry = "SELECT count(*) FROM %s" % vtiger_module
        if self.vtiger_progress_from_date:
            qry += " WHERE modifiedtime >= '%s'" % fields.Datetime.to_string(
                self.vtiger_progress_from_date
            )
        qry += ";"
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        req = Request("%s?%s" % (self.get_vtiger_server_url(), data))
        response = urlopen(req, timeout=20)
        result = json.loads(response.read())
        if not result.get("success") or not result.get("result"):
            return 0
        row = result["result"][0]
        count_value = (
            row.get("count")
            or row.get("count(*)")
            or row.get("COUNT(*)")
            or row.get("total")
            or 0
        )
        try:
            return int(float(count_value))
        except (TypeError, ValueError):
            return 0

    def _execute_vtiger_id_query(self, vtiger_module, session_name):
        qry = "SELECT id FROM %s" % vtiger_module
        if self.vtiger_progress_from_date:
            qry += " WHERE modifiedtime >= '%s'" % fields.Datetime.to_string(
                self.vtiger_progress_from_date
            )
        qry += ";"
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        req = Request("%s?%s" % (self.get_vtiger_server_url(), data))
        response = urlopen(req, timeout=20)
        result = json.loads(response.read())
        if not result.get("success"):
            return []
        return [row.get("id") for row in result.get("result", []) if row.get("id")]

    def _execute_vtiger_record_query(self, vtiger_module, session_name):
        qry = "SELECT * FROM %s" % vtiger_module
        if self.vtiger_progress_from_date:
            qry += " WHERE modifiedtime >= '%s'" % fields.Datetime.to_string(
                self.vtiger_progress_from_date
            )
        qry += ";"
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        req = Request("%s?%s" % (self.get_vtiger_server_url(), data))
        response = urlopen(req, timeout=20)
        result = json.loads(response.read())
        if not result.get("success"):
            return []
        return result.get("result", [])

    def _get_vtiger_progress_source_ids(self, definition, session_name):
        source_ids = []
        for vtiger_module in definition["modules"]:
            for vtiger_id in self._execute_vtiger_id_query(vtiger_module, session_name):
                source_ids.append(
                    definition.get("id_format", "%s").replace(
                        "%(module)s", vtiger_module
                    )
                    % vtiger_id
                )
        return source_ids

    def _get_vtiger_progress_source_records(self, definition, session_name):
        source_records = []
        for vtiger_module in definition["modules"]:
            for record in self._execute_vtiger_record_query(
                vtiger_module, session_name
            ):
                source_records.append((vtiger_module, record))
        return source_records

    def _find_odoo_record_from_vtiger_record(self, model, vtiger_module, record):
        vtiger_id = record.get("id")
        if vtiger_id and "vtiger_id" in model._fields:
            existing = model.search([("vtiger_id", "=", vtiger_id)], limit=1)
            if existing:
                return existing

        model_name = model._name
        if model_name == "res.partner":
            return self._find_progress_partner(vtiger_module, record, model)
        if model_name == "product.template":
            return self._find_progress_product(vtiger_module, record, model)
        if model_name == "product.pricelist":
            name = record.get("bookname") or record.get("pricebookname")
            return self._find_progress_by_name(model, name)
        if model_name == "crm.lead":
            return self._find_progress_crm(vtiger_module, record, model)
        if model_name == "sale.order":
            return self._find_progress_sale_order(vtiger_module, record, model)
        if model_name == "purchase.order":
            return self._find_progress_purchase_order(record, model)
        if model_name == "account.move":
            return self._find_progress_invoice(record, model)
        if model_name == "calendar.event":
            return self._find_progress_calendar_event(record, model)
        if model_name == "project.project":
            return self._find_progress_by_name(model, record.get("projectname"))
        if model_name == "project.task":
            return self._find_progress_by_name(
                model, record.get("subject") or record.get("taskname")
            )
        if model_name == "helpdesk.ticket":
            return self._find_progress_by_name(model, record.get("ticket_title"))
        return model.browse()

    def _find_progress_by_name(self, model, name):
        if not name or "name" not in model._fields:
            return model.browse()
        return model.search(
            [("name", "=ilike", name), ("vtiger_id", "=", False)],
            limit=1,
        )

    def _find_progress_partner(self, vtiger_module, record, model):
        if vtiger_module == "Accounts":
            name = record.get("accountname") or record.get("account_no")
            email = record.get("email1")
            base_domain = [("is_company", "=", True)]
        elif vtiger_module == "Vendors":
            name = record.get("vendorname") or record.get("vendor_no")
            email = record.get("email")
            base_domain = []
        else:
            name = " ".join(
                part
                for part in (record.get("firstname"), record.get("lastname"))
                if part
            )
            email = record.get("email")
            base_domain = []
        for field_name, value in (
            ("email", email),
            ("mobile", record.get("mobile")),
            ("phone", record.get("phone")),
            ("name", name),
        ):
            if value:
                partner = model.search(
                    base_domain
                    + [(field_name, "=ilike", value), ("vtiger_id", "=", False)],
                    limit=1,
                )
                if partner:
                    return partner
        return model.browse()

    def _find_progress_product(self, vtiger_module, record, model):
        name = (
            record.get("servicename")
            if vtiger_module == "Services"
            else record.get("productname")
        )
        if record.get("serial_no"):
            product = model.search(
                [
                    ("default_code", "=ilike", record.get("serial_no")),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
            if product:
                return product
        if name:
            return model.search(
                [
                    ("name", "=ilike", name),
                    ("list_price", "=", float(record.get("unit_price") or 0.0)),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        return model.browse()

    def _find_progress_crm(self, vtiger_module, record, model):
        if vtiger_module == "Potentials":
            name = record.get("potentialname")
            crm_type = "opportunity"
        else:
            name = " ".join(
                part
                for part in (record.get("firstname"), record.get("lastname"))
                if part
            ) or record.get("company")
            crm_type = "lead"
        for field_name, value in (
            ("email_from", record.get("email")),
            ("phone", record.get("phone")),
            ("mobile", record.get("mobile")),
            ("name", name),
        ):
            if value:
                crm = model.search(
                    [
                        ("type", "=", crm_type),
                        (field_name, "=ilike", value),
                        ("vtiger_id", "=", False),
                    ],
                    limit=1,
                )
                if crm:
                    return crm
        return model.browse()

    def _find_progress_sale_order(self, vtiger_module, record, model):
        order_ref = (
            record.get("salesorder_no")
            or record.get("quote_no")
            or record.get("subject")
            or record.get("id")
        )
        domain = [("vtiger_id", "=", False)]
        if "client_order_ref" in model._fields and order_ref:
            sale_order = model.search(
                domain + [("client_order_ref", "=ilike", order_ref)], limit=1
            )
            if sale_order:
                return sale_order
        partner = self.env["res.partner"].search(
            [
                (
                    "vtiger_id",
                    "in",
                    [record.get("contact_id"), record.get("account_id")],
                )
            ],
            limit=1,
        )
        if partner and record.get("createdtime"):
            return model.search(
                domain
                + [
                    ("partner_id", "=", partner.id),
                    ("date_order", "=", record.get("createdtime")),
                    ("amount_total", "=", float(record.get("hdnGrandTotal") or 0.0)),
                ],
                limit=1,
            )
        return model.browse()

    def _find_progress_purchase_order(self, record, model):
        order_ref = (
            record.get("purchaseorder_no") or record.get("subject") or record.get("id")
        )
        if order_ref:
            return model.search(
                [("partner_ref", "=ilike", order_ref), ("vtiger_id", "=", False)],
                limit=1,
            )
        return model.browse()

    def _find_progress_invoice(self, record, model):
        invoice_ref = (
            record.get("invoice_no") or record.get("subject") or record.get("id")
        )
        if invoice_ref:
            return model.search(
                [
                    ("ref", "=ilike", invoice_ref),
                    ("move_type", "=", "out_invoice"),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        return model.browse()

    def _find_progress_calendar_event(self, record, model):
        if not record.get("subject"):
            return model.browse()
        domain = [("name", "=ilike", record.get("subject")), ("vtiger_id", "=", False)]
        if record.get("date_start"):
            domain.append(("start", ">=", record.get("date_start")))
        return model.search(domain, limit=1)

    def _count_odoo_vtiger_records(
        self, definition, source_ids=False, source_records=False
    ):
        model_names = definition.get("models") or (definition.get("model"),)
        total = 0
        source_ids = list(dict.fromkeys(source_ids or []))
        source_records = source_records or []
        if not source_ids and not source_records:
            return total
        seen_records = set()
        for model_name in model_names:
            if not model_name or model_name not in self.env:
                continue
            model = self.env[model_name]
            if "vtiger_id" not in model._fields:
                continue
            records = model.search([("vtiger_id", "in", source_ids)])
            seen_records.update(records.ids)
            for vtiger_module, source_record in source_records:
                odoo_record = self._find_odoo_record_from_vtiger_record(
                    model, vtiger_module, source_record
                )
                seen_records.update(odoo_record.ids)
        total = len(seen_records)
        return total

    def action_check_vtiger_sync_progress(self):
        for company in self:
            company._check_vtiger_connection_config()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            vals = {"last_vtiger_progress_check": fields.Datetime.now()}
            for (
                field_name,
                definition,
            ) in company._vtiger_progress_definitions().items():
                if not all(
                    model in company.env for model in definition.get("models", ())
                ):
                    continue
                if definition.get("model") and definition["model"] not in company.env:
                    continue
                source_ids = company._get_vtiger_progress_source_ids(
                    definition, session_name
                )
                source_records = company._get_vtiger_progress_source_records(
                    definition, session_name
                )
                vtiger_total = len(source_ids)
                odoo_total = company._count_odoo_vtiger_records(
                    definition,
                    source_ids=source_ids,
                    source_records=source_records,
                )
                vals[field_name] = (
                    100.0
                    if not vtiger_total
                    else min(100.0, (odoo_total / vtiger_total) * 100.0)
                )
            company.write(vals)
        return True
