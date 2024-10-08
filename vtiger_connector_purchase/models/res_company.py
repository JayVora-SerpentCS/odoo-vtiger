# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


# Todo: Need to set tax in odoo of vtiger in purchase order.
class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_purchase_order()

    def update_existing_order(self, result):
        """Added the Method for the Work Existing order line,
        Because the Vtiger return dictionary"""
        purchase_order_obj = self.env["purchase.order"]
        for res in result.get("result", []):
            order_id = purchase_order_obj.search(
                [("vtiger_id", "=", res.get("id"))], limit=1
            )
            if order_id:
                order_id.order_line.unlink()
        return True

    def _build_query(self, company):
        """Build query based on the last sync date."""
        if company.last_sync_date:
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

    def _sync_order_lines(self, res, order_id, company):
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
                    company.sync_vtiger_products(
                        company, vtiger_type=["Products", "Services"]
                    )

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

    def sync_vtiger_purchase_order(self):
        purchase_order_obj = self.env["purchase.order"]
        partner_obj = self.env["res.partner"]
        user_obj = self.env["res.users"]
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = self._build_query(company)
            result = self._execute_vtiger_query(company, qry, session_name)
            if result.get("success"):
                self.update_existing_order(result)
                for res in result.get("result", []):
                    order_id = purchase_order_obj.search(
                        [("vtiger_id", "=", res.get("id"))], limit=1
                    )
                    po_order_vals = {}
                    if res.get("contact_id") or res.get("vendor_id"):
                        partner_exist = partner_obj.search(
                            [
                                "|",
                                ("vtiger_id", "=", res.get("contact_id")),
                                ("vtiger_id", "=", res.get("vendor_id")),
                            ],
                            limit=2,
                        )
                        if not partner_exist:
                            company.sync_vtiger_partner()
                    if not order_id:
                        contact_id = res.get("vendor_id")
                        if contact_id:
                            partner = partner_obj.search(
                                [("vtiger_id", "=", contact_id)], limit=1
                            )
                            if partner:
                                po_order_vals.update({"partner_id": partner.id})
                        else:
                            vtiger_user = user_obj.search(
                                [("login", "=", "vtigeruser@vtiger")]
                            )
                            if not vtiger_user:
                                vtiger_user = user_obj.create(
                                    {
                                        "name": "VTiger-User",
                                        "login": "vtigeruser@vtiger",
                                    }
                                )
                            po_order_vals.update(
                                {"partner_id": vtiger_user.partner_id.id}
                            )
                        date_o = res.get("createdtime")
                        if date_o:
                            po_order_vals.update({"date_order": date_o})
                        date_modified = res.get("modifiedtime")
                        if date_modified:
                            po_order_vals.update({"date_planned": date_modified})
                        po_order_vals.update(
                            {
                                "vtiger_id": res.get("id"),
                                "notes": res.get("terms_conditions"),
                            }
                        ),
                        order_id = purchase_order_obj.create(po_order_vals)

                    if res.get("lineItems"):
                        self._sync_order_lines(res, order_id, company)
        return True
