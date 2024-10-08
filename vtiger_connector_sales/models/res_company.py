# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_sale_order()

    def update_existing_sale_order_and_quotes(self, result):
        """Added the Method for the Work Existing order line,
        Because the Vtiger return dictionary"""
        sale_order_obj = self.env["sale.order"]
        for res in result.get("result", []):
            order_id = sale_order_obj.search(
                [("vtiger_id", "=", res.get("id"))], limit=1
            )
            if order_id:
                order_id.order_line.unlink()
        return True

    def _build_query_sales(self, company, vtiger_type):
        """Build query based on the last sync date."""
        if company.last_sync_date:
            qry_template = {
                "SalesOrder": """SELECT * FROM SalesOrder WHERE modifiedtime >= '{}';""",
                "Quotes": """SELECT * FROM Quotes WHERE modifiedtime >= '{}';""",
            }
            return qry_template[vtiger_type].format(company.last_sync_date)
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
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _sync_sale_order_line(self, res, order_id, company):
        """Sync the order lines from VTiger to Odoo."""
        product_obj = self.env["product.product"]
        netprice = res.get("hdnGrandTotal")
        if res.get("lineItems"):
            for order_line_dict in res.get("lineItems"):
                if type(order_line_dict) != dict:
                    order_line_dict = res.get("lineItems").get(order_line_dict)
                product = product_obj.search(
                    [("vtiger_id", "=", order_line_dict.get("productid"))],
                    limit=1,
                )
                if not product:
                    company.sync_vtiger_products(
                        company, vtiger_type=["Products", "Services"]
                    )
                price_unit = order_line_dict.get("listprice")
                quantity = order_line_dict.get("quantity")

                order_line_vals = {
                    "name": order_line_dict.get("comment"),
                    "product_id": product and product.id,
                    "product_uom": product.uom_id.id or 0,
                    "product_uom_qty": float(quantity or 0.00),
                    "price_unit": float(price_unit or 0.00),
                    "price_subtotal": float(netprice or 0.00),
                    "order_id": order_id.id,
                }
                if order_id:
                    order_id.write({"order_line": [(0, 0, order_line_vals)]})

    def fetch_so_and_quotes_data(self, company, vtiger_type):
        sale_order_obj = self.env["sale.order"]
        partner_obj = self.env["res.partner"]
        lead_obj = self.env["crm.lead"]
        user_obj = self.env["res.users"]
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        qry = self._build_query_sales(company, vtiger_type)
        result = self._execute_vtiger_query_sales(company, qry, session_name)
        if result.get("success"):
            self.update_existing_sale_order_and_quotes(result)
            for res in result.get("result", []):
                if res.get("contact_id") and vtiger_type == "SalesOrder":
                    partner_exist = partner_obj.search(
                        [("vtiger_id", "=", res.get("contact_id"))], limit=1
                    )
                    if not partner_exist:
                        company.sync_vtiger_partner()
                if res.get("quotestage") == "New" or vtiger_type == "SalesOrder":
                    order_id = sale_order_obj.search(
                        [("vtiger_id", "=", res.get("id"))], limit=1
                    )
                    so_order_vals = {}
                    if not order_id:
                        contact_id = res.get("contact_id")
                        if contact_id:
                            partner = partner_obj.search(
                                [("vtiger_id", "=", contact_id)], limit=1
                            )
                            if partner:
                                so_order_vals.update({"partner_id": partner.id})
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
                            so_order_vals.update(
                                {"partner_id": vtiger_user.partner_id.id}
                            )
                        date_o = res.get("createdtime")
                        if date_o:
                            so_order_vals.update({"date_order": date_o})
                        date_due = res.get("duedate")
                        if date_due:
                            so_order_vals.update({"validity_date": date_due})
                        opportunity_id = res.get("potential_id")
                        if opportunity_id:
                            opportunity = lead_obj.search(
                                [("vtiger_id", "=", opportunity_id)], limit=1
                            )
                            if opportunity:
                                so_order_vals.update({"opportunity_id": opportunity.id})
                        if vtiger_type == "SalesOrder":
                            so_order_vals.update(
                                {
                                    "vtiger_id": res.get("id"),
                                    "note": res.get("terms_conditions"),
                                }
                            ),
                        else:
                            so_order_vals.update(
                                {
                                    "vtiger_id": res.get("id"),
                                    "note": res.get("terms_conditions"),
                                    "state": "draft",
                                }
                            ),
                        order_id = sale_order_obj.create(so_order_vals)
                    self._sync_sale_order_line(res, order_id, company)
                    if (
                        vtiger_type == "SalesOrder"
                        and res.get("sostatus") == "Approved"
                    ):
                        order_id.sudo().action_confirm()
            return True

    def sync_vtiger_sale_order(self):
        for company in self:
            company.fetch_so_and_quotes_data(company, vtiger_type="SalesOrder")
            company.sync_vtiger_sale_Quotes()
        return True

    def sync_vtiger_sale_Quotes(self):
        for company in self:
            company.fetch_so_and_quotes_data(company, vtiger_type="Quotes")
        return True
