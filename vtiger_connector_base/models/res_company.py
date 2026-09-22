# See LICENSE file for full copyright and licensing details.

import json
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests

from odoo import api, fields, models

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
    vtiger_document_progress = fields.Float(string="Documents", readonly=True)

    def get_vtiger_server_url(self):
        return "%s/%s" % (self.vtiger_server, URL)

    def get_vtiger_access_key(self):
        """Get the token using 'getchallenge' operation"""
        self.ensure_one()
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
            "vtiger_document_progress": {
                "modules": ("Documents",),
                "model": "documents.document",
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

    def _count_odoo_vtiger_records(self, definition, source_ids=False):
        model_names = definition.get("models") or (definition.get("model"),)
        total = 0
        source_ids = list(dict.fromkeys(source_ids or []))
        if not source_ids:
            return total
        for model_name in model_names:
            if not model_name or model_name not in self.env:
                continue
            model = self.env[model_name]
            if "vtiger_id" not in model._fields:
                continue
            total += model.search_count([("vtiger_id", "in", source_ids)])
        return total

    def action_check_vtiger_sync_progress(self):
        for company in self:
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
                vtiger_total = len(source_ids)
                odoo_total = company._count_odoo_vtiger_records(
                    definition, source_ids=source_ids
                )
                vals[field_name] = (
                    100.0
                    if not vtiger_total
                    else min(100.0, (odoo_total / vtiger_total) * 100.0)
                )
            company.write(vals)
        return True
