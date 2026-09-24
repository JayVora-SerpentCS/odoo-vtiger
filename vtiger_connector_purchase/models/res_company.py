# See LICENSE file for full copyright and licensing details.

from urllib.parse import urlencode
from urllib.request import Request

from odoo import fields, models


# Todo: Need to set tax in odoo of vtiger in purchase order.
class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        self.sync_vtiger_purchase_order(full_sync=False)
        return super().action_sync_vtiger()

    def update_existing_order(self, order_id):
        """Refresh lines only for the current editable purchase order."""
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
            "note": res.get("terms_conditions"),
        }
        date_o = res.get("createdtime") or res.get("orderdate")
        if date_o:
            vals["date_order"] = date_o
        date_planned = res.get("duedate") or res.get("modifiedtime")
        if date_planned:
            vals["date_planned"] = date_planned
        return vals

    def _build_query(self, company, full_sync=True):
        """Build query based on the last sync date."""
        if company.last_sync_date and not full_sync:
            return """SELECT * FROM PurchaseOrder WHERE modifiedtime >= '%s';""" % (
                fields.Datetime.to_string(company.last_sync_date)
            )
        return """SELECT * FROM PurchaseOrder;"""

    def _execute_vtiger_query(self, company, qry, session_name):
        """Execute the query on VTiger."""
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        return company._vtiger_request_json(req, "querying VTiger")

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

    def _iter_vtiger_order_lines(self, res):
        line_items = res.get("lineItems") or []
        if isinstance(line_items, dict):
            line_items = line_items.values()
        for order_line_dict in line_items:
            if isinstance(order_line_dict, dict):
                yield order_line_dict

    def _sync_order_lines(self, res, order_id, company, session_name):
        """Sync the order lines from VTiger to Odoo."""
        product_obj = self.env["product.product"]
        order_line_vals = []
        date_planned = (
            order_id.date_planned or order_id.date_order or fields.Datetime.now()
        )

        for order_line_dict in self._iter_vtiger_order_lines(res):
            vtiger_product_id = order_line_dict.get("productid")
            if not vtiger_product_id:
                continue
            product = product_obj.search(
                [("vtiger_id", "=", vtiger_product_id)], limit=1
            )
            if not product:
                product = company._sync_vtiger_product_reference(
                    company, vtiger_product_id, session_name
                )
            if not product:
                continue

            price_unit = order_line_dict.get("listprice")
            quantity = order_line_dict.get("quantity")
            order_line_vals.append(
                (
                    0,
                    0,
                    {
                        "name": order_line_dict.get("comment") or product.display_name,
                        "product_id": product.id,
                        "product_uom_id": product.uom_id.id,
                        "product_qty": float(quantity or 0.00),
                        "price_unit": float(price_unit or 0.00),
                        "date_planned": fields.Datetime.to_string(date_planned),
                    },
                )
            )

        if order_line_vals:
            order_id.write({"order_line": order_line_vals})

    def sync_vtiger_purchase_order(self, full_sync=True):
        purchase_order_obj = self.env["purchase.order"]
        for company in self:
            if self.env.user.company_id != company:
                continue
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = self._build_query(company, full_sync=full_sync)
            result = self._execute_vtiger_query(company, qry, session_name)
            if not result.get("success"):
                continue
            for res in result.get("result", []):
                po_order_vals = self._prepare_purchase_order_values(
                    company, res, session_name
                )
                order_id = self._find_existing_vtiger_purchase_order(res, po_order_vals)
                if order_id:
                    if not order_id.vtiger_id:
                        po_order_vals["vtiger_id"] = res.get("id")
                    if order_id.state in ("draft", "sent", "to approve"):
                        order_id.write(po_order_vals)
                    else:
                        update_vals = {}
                        if res.get("terms_conditions"):
                            update_vals["note"] = res.get("terms_conditions")
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
                    if order_id.state in ("draft", "sent", "to approve"):
                        self.update_existing_order(order_id)
                    self._sync_order_lines(res, order_id, company, session_name)
        return True
