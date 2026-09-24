# See LICENSE file for full copyright and licensing details.

from urllib.parse import urlencode
from urllib.request import Request

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        self.sync_vtiger_sale_order(full_sync=False)
        return super().action_sync_vtiger()

    def update_existing_sale_order_and_quotes(self, order_id):
        """Refresh lines only for the current editable order."""
        if order_id and order_id.state in ("draft", "sent"):
            order_id.order_line.unlink()
        return True

    def _get_vtiger_fallback_partner(self):
        vtiger_user = self.env["res.users"].search(
            [("login", "=", "vtigeruser@vtiger")], limit=1
        )
        if not vtiger_user:
            vtiger_user = self.env["res.users"].create(
                {
                    "name": "VTiger-User",
                    "login": "vtigeruser@vtiger",
                }
            )
        return vtiger_user.partner_id

    def _get_sale_order_partner(self, company, res, session_name):
        partner_obj = self.env["res.partner"]
        for vtiger_module, vtiger_id in (
            ("Contacts", res.get("contact_id")),
            ("Accounts", res.get("account_id")),
        ):
            if not vtiger_id:
                continue
            partner = partner_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
            if not partner and hasattr(company, "_sync_vtiger_partner_reference"):
                partner = company._sync_vtiger_partner_reference(
                    company, vtiger_module, vtiger_id, session_name
                )
            if partner:
                return partner
        return self._get_vtiger_fallback_partner()

    def _prepare_sale_order_values(self, company, res, vtiger_type, session_name):
        lead_obj = self.env["crm.lead"]
        partner = self._get_sale_order_partner(company, res, session_name)
        order_ref = (
            res.get("salesorder_no")
            or res.get("quote_no")
            or res.get("subject")
            or res.get("id")
        )
        vals = {
            "partner_id": partner.id,
            "client_order_ref": order_ref,
            "note": res.get("terms_conditions"),
            "vtiger_record_type": vtiger_type,
            "vtiger_status": res.get("quotestage") or res.get("sostatus"),
        }
        date_o = res.get("createdtime")
        if date_o:
            vals["date_order"] = date_o
        date_due = res.get("duedate")
        if date_due:
            vals["validity_date"] = date_due
        opportunity_id = res.get("potential_id")
        if opportunity_id:
            opportunity = lead_obj.search([("vtiger_id", "=", opportunity_id)], limit=1)
            if opportunity:
                vals["opportunity_id"] = opportunity.id
        return vals

    def _get_vtiger_sale_target_state(self, res, vtiger_type):
        if vtiger_type == "SalesOrder":
            status = str(res.get("sostatus") or "").strip().lower()
            if status in ("cancelled", "canceled"):
                return "cancel"
            return "sale"
        quote_stage = str(res.get("quotestage") or "").strip().lower()
        if quote_stage in ("rejected", "cancelled", "canceled", "closed lost"):
            return "cancel"
        if quote_stage in (
            "accepted",
            "approved",
            "delivered",
            "reviewed",
            "sent",
            "accepted quote",
        ):
            return "sent"
        return "draft"

    def _apply_vtiger_sale_state(self, order_id, res, vtiger_type):
        target_state = self._get_vtiger_sale_target_state(res, vtiger_type)
        if target_state == "sale" and order_id.state in ("draft", "sent"):
            order_id.sudo().action_confirm()
        elif target_state == "sent" and order_id.state == "draft":
            order_id.write({"state": "sent"})
        elif target_state == "cancel" and order_id.state != "cancel":
            order_id.sudo().action_cancel()

    def _build_query_sales(self, company, vtiger_type, full_sync=True):
        """Build query based on the last sync date."""
        if company.last_sync_date and not full_sync:
            qry_template = {
                "SalesOrder": """SELECT * FROM SalesOrder WHERE modifiedtime >= '{}';""",
                "Quotes": """SELECT * FROM Quotes WHERE modifiedtime >= '{}';""",
            }
            return qry_template[vtiger_type].format(
                fields.Datetime.to_string(company.last_sync_date)
            )
        qry_template_1 = {
            "SalesOrder": """SELECT * FROM SalesOrder;""",
            "Quotes": """SELECT * FROM Quotes;""",
        }
        return qry_template_1[vtiger_type]

    def _execute_vtiger_query_sales(self, company, qry, session_name):
        """Execute the query on VTiger."""
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        return company._vtiger_request_json(req, "querying VTiger")

    def _find_existing_vtiger_sale_order(self, res, so_order_vals):
        sale_order_obj = self.env["sale.order"]
        order = sale_order_obj.search([("vtiger_id", "=", res.get("id"))], limit=1)
        if order:
            return order
        order_ref = so_order_vals.get("client_order_ref")
        if order_ref:
            order = sale_order_obj.search(
                [
                    ("client_order_ref", "=ilike", order_ref),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
            if order:
                return order
        if (
            so_order_vals.get("partner_id")
            and so_order_vals.get("date_order")
            and res.get("hdnGrandTotal")
        ):
            return sale_order_obj.search(
                [
                    ("partner_id", "=", so_order_vals["partner_id"]),
                    ("date_order", "=", so_order_vals["date_order"]),
                    ("amount_total", "=", float(res.get("hdnGrandTotal") or 0.0)),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        return sale_order_obj

    def _sync_sale_order_line(self, res, order_id, company, session_name):
        """Sync the order lines from VTiger to Odoo."""
        product_obj = self.env["product.product"]
        if res.get("lineItems"):
            for order_line_dict in res.get("lineItems"):
                if not isinstance(order_line_dict, dict):
                    order_line_dict = res.get("lineItems").get(order_line_dict)
                product = product_obj.search(
                    [("vtiger_id", "=", order_line_dict.get("productid"))],
                    limit=1,
                )
                if not product:
                    product = company._sync_vtiger_product_reference(
                        company, order_line_dict.get("productid"), session_name
                    )
                if not product:
                    continue
                price_unit = order_line_dict.get("listprice")
                quantity = order_line_dict.get("quantity")

                order_line_vals = {
                    "name": order_line_dict.get("comment"),
                    "product_id": product and product.id,
                    "product_uom_id": product.uom_id.id or 0,
                    "product_uom_qty": float(quantity or 0.00),
                    "price_unit": float(price_unit or 0.00),
                    "order_id": order_id.id,
                }
                if order_id:
                    order_id.write({"order_line": [(0, 0, order_line_vals)]})

    def fetch_so_and_quotes_data(
        self, company, vtiger_type, full_sync=True
    ):  # noqa: C901
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        qry = self._build_query_sales(company, vtiger_type, full_sync=full_sync)
        result = self._execute_vtiger_query_sales(company, qry, session_name)
        if result.get("success"):
            for res in result.get("result", []):
                so_order_vals = self._prepare_sale_order_values(
                    company, res, vtiger_type, session_name
                )
                order_id = self._find_existing_vtiger_sale_order(res, so_order_vals)
                if order_id.state not in ("sale", "cancel"):
                    self.update_existing_sale_order_and_quotes(order_id)
                if order_id:
                    if not order_id.vtiger_id:
                        so_order_vals["vtiger_id"] = res.get("id")
                    if order_id.state in ("draft", "sent"):
                        order_id.write(so_order_vals)
                    else:
                        update_vals = {
                            "note": so_order_vals.get("note"),
                            "vtiger_status": so_order_vals.get("vtiger_status"),
                            "vtiger_record_type": vtiger_type,
                        }
                        if not order_id.vtiger_id:
                            update_vals["vtiger_id"] = res.get("id")
                        order_id.write(update_vals)
                else:
                    so_order_vals["vtiger_id"] = res.get("id")
                    order_id = self.env["sale.order"].create(so_order_vals)
                if order_id.state not in ("sale", "cancel") or not order_id.order_line:
                    self._sync_sale_order_line(res, order_id, company, session_name)
                self._apply_vtiger_sale_state(order_id, res, vtiger_type)
            return True

    def sync_vtiger_sale_order(self, full_sync=True):
        for company in self:
            if self.env.user.company_id == company:
                company.fetch_so_and_quotes_data(
                    company, vtiger_type="SalesOrder", full_sync=full_sync
                )
                company.sync_vtiger_sale_Quotes(full_sync=full_sync)
        return True

    def sync_vtiger_sale_Quotes(self, full_sync=True):
        for company in self:
            company.fetch_so_and_quotes_data(
                company, vtiger_type="Quotes", full_sync=full_sync
            )
        return True
