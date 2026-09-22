# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


# Todo: Need to set tax in odoo of vtiger in purchase order.
class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        self.sync_vtiger_purchase_order(full_sync=False)
        return super(ResCompany, self).action_sync_vtiger()

    def update_existing_order(self, result):
        """Added the Method for the Work Existing order line,
        Because the Vtiger return dictionary"""
        purchase_order_obj = self.env["purchase.order"]
        for res in result.get("result", []):
            order_id = purchase_order_obj.search(
                [("vtiger_id", "=", res.get("id"))], limit=1
            )
            if order_id and order_id.state in ("draft", "sent", "to approve"):
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

    def _get_purchase_order_partner(self, company, res, session_name):
        partner_obj = self.env["res.partner"]
        for vtiger_module, vtiger_id in (
            ("Vendors", res.get("vendor_id")),
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

    def _prepare_purchase_order_values(self, company, res, session_name):
        partner = self._get_purchase_order_partner(company, res, session_name)
        vals = {
            "partner_id": partner.id,
            "partner_ref": res.get("purchaseorder_no")
            or res.get("subject")
            or res.get("id"),
            "notes": res.get("terms_conditions"),
        }
        date_o = res.get("createdtime")
        if date_o:
            vals["date_order"] = date_o
        date_modified = res.get("modifiedtime")
        if date_modified:
            vals["date_planned"] = date_modified
        return vals

    def _build_query(self, company, full_sync=True):
        """Build query based on the last sync date."""
        if company.last_sync_date and not full_sync:
            return """SELECT * FROM PurchaseOrder WHERE modifiedtime >= '%s';""" % (
                company.last_sync_date
            )
        return """SELECT * FROM PurchaseOrder;"""

    def _execute_vtiger_query(self, company, qry, session_name):
        """Execute the query on VTiger."""
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _find_existing_vtiger_purchase_order(self, res, po_order_vals):
        purchase_order_obj = self.env["purchase.order"]
        order = purchase_order_obj.search([("vtiger_id", "=", res.get("id"))], limit=1)
        if order:
            return order
        if po_order_vals.get("partner_ref"):
            order = purchase_order_obj.search(
                [
                    ("partner_ref", "=ilike", po_order_vals["partner_ref"]),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
            if order:
                return order
        if (
            po_order_vals.get("partner_id")
            and po_order_vals.get("date_order")
            and res.get("hdnGrandTotal")
        ):
            return purchase_order_obj.search(
                [
                    ("partner_id", "=", po_order_vals["partner_id"]),
                    ("date_order", "=", po_order_vals["date_order"]),
                    ("amount_total", "=", float(res.get("hdnGrandTotal") or 0.0)),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        return purchase_order_obj

    def _sync_order_lines(self, res, order_id, company, session_name):
        """Sync the order lines from VTiger to Odoo."""
        product_obj = self.env["product.product"]
        if res.get("lineItems"):
            for order_line_dict in res.get("lineItems"):
                if type(order_line_dict) != dict:
                    order_line_dict = res.get("lineItems").get(order_line_dict)
                product = product_obj.search(
                    [("vtiger_id", "=", order_line_dict.get("productid"))], limit=1
                )
                if not product:
                    product = company._sync_vtiger_product_reference(
                        company, order_line_dict.get("productid"), session_name
                    )
                if not product:
                    continue

                price_unit = order_line_dict.get("listprice")
                quantity = order_line_dict.get("quantity")
                netprice = res.get("hdnGrandTotal")

                order_line_vals = {
                    "name": order_line_dict.get("comment"),
                    "product_id": product and product.id,
                    "product_uom": product.uom_id.id,
                    "product_qty": float(quantity or 0.00),
                    "price_unit": float(price_unit or 0.00),
                    "price_subtotal": float(netprice or 0.00),
                    "order_id": order_id.id,
                    "date_planned": order_id.date_order.strftime("%Y-%m-%d %H:%M:%S"),
                }

                order_id.write({"order_line": [(0, 0, order_line_vals)]})

    def sync_vtiger_purchase_order(self, full_sync=True):
        purchase_order_obj = self.env["purchase.order"]
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = self._build_query(company, full_sync=full_sync)
            result = self._execute_vtiger_query(company, qry, session_name)
            if result.get("success"):
                self.update_existing_order(result)
                for res in result.get("result", []):
                    order_id = purchase_order_obj.search(
                        [("vtiger_id", "=", res.get("id"))], limit=1
                    )
                    po_order_vals = self._prepare_purchase_order_values(
                        company, res, session_name
                    )
                    if not order_id:
                        order_id = self._find_existing_vtiger_purchase_order(
                            res, po_order_vals
                        )
                    if order_id:
                        if not order_id.vtiger_id:
                            po_order_vals["vtiger_id"] = res.get("id")
                        if order_id.state in ("draft", "sent", "to approve"):
                            order_id.write(po_order_vals)
                        else:
                            update_vals = {}
                            if res.get("terms_conditions"):
                                update_vals["notes"] = res.get("terms_conditions")
                            if not order_id.vtiger_id:
                                update_vals["vtiger_id"] = res.get("id")
                            if update_vals:
                                order_id.write(update_vals)
                    else:
                        po_order_vals["vtiger_id"] = res.get("id")
                        order_id = purchase_order_obj.create(po_order_vals)

                    if res.get("lineItems") and (
                        order_id.state in ("draft", "sent", "to approve")
                        or not order_id.order_line
                    ):
                        self._sync_order_lines(res, order_id, company, session_name)
        return True
