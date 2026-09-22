# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


# Todo: Need to set tax in odoo of vtiger in product.
class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        self.sync_vtiger_service_products()
        return super(ResCompany, self).action_sync_vtiger()

    def service_product_vals(self, res):
        return {
            "name": res.get("servicename", ""),
            "sale_ok": True,
            "purchase_ok": True,
            "type": "service",
            "default_code": res.get("serial_no"),
            "list_price": res.get("unit_price"),
            "standard_price": res.get("purchase_cost"),
            "description_sale": res.get("description"),
        }

    def product_vals(self, res):
        return {
            "name": res.get("productname", ""),
            "sale_ok": True,
            "purchase_ok": True,
            "type": "consu",
            "default_code": res.get("serial_no"),
            "list_price": res.get("unit_price"),
            "standard_price": res.get("purchase_cost"),
            "description_sale": res.get("description"),
        }

    def _execute_vtiger_product_query(self, company, qry, session_name):
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _upsert_vtiger_product_template(self, vtiger_product_type, res):
        product_templ_obj = self.env["product.template"]
        if vtiger_product_type == "Services":
            product_vals = self.service_product_vals(res)
        else:
            product_vals = self.product_vals(res)
        if not product_vals.get("name"):
            product_vals["name"] = res.get("label") or res.get("id")
        product = product_templ_obj.search([("vtiger_id", "=", res.get("id"))], limit=1)
        if not product and product_vals.get("default_code"):
            product = product_templ_obj.search(
                [
                    ("default_code", "=ilike", product_vals["default_code"]),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        if not product and product_vals.get("name"):
            product = product_templ_obj.search(
                [
                    ("name", "=ilike", product_vals["name"]),
                    ("list_price", "=", float(product_vals.get("list_price") or 0.0)),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        if product:
            if not product.vtiger_id:
                product_vals["vtiger_id"] = res.get("id")
            product.write(product_vals)
        else:
            product_vals["vtiger_id"] = res.get("id")
            product = product_templ_obj.create(product_vals)
        return product

    def _sync_vtiger_product_reference(self, company, vtiger_id, session_name=False):
        if not vtiger_id:
            return self.env["product.product"]
        product_variant = self.env["product.product"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if product_variant:
            return product_variant
        if not session_name:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
        for vtiger_product_type in ("Products", "Services"):
            qry = "SELECT * FROM %s WHERE id = '%s';" % (
                vtiger_product_type,
                vtiger_id,
            )
            result = company._execute_vtiger_product_query(company, qry, session_name)
            if result.get("success") and result.get("result"):
                template = company._upsert_vtiger_product_template(
                    vtiger_product_type, result["result"][0]
                )
                return template.product_variant_id
        return self.env["product.product"]

    def sync_vtiger_products(self, company, vtiger_type):
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        qry_template = {
            "Products": """SELECT * FROM Products WHERE modifiedtime >= '{}';""",
            "Services": """SELECT * FROM Services WHERE modifiedtime >= '{}';""",
        }
        qry_template_1 = {
            "Products": """SELECT * FROM Products;""",
            "Services": """SELECT * FROM Services;""",
        }
        for vtiger_product_type in vtiger_type:
            if company.last_sync_date:
                qry = qry_template[vtiger_product_type].format(company.last_sync_date)
            else:
                qry = qry_template_1[vtiger_product_type]
            result = company._execute_vtiger_product_query(company, qry, session_name)
            if result.get("success"):
                for res in result.get("result", []):
                    self._upsert_vtiger_product_template(vtiger_product_type, res)
        return True

    def sync_vtiger_service_products(self):
        for company in self:
            self.sync_vtiger_products(company, vtiger_type=["Products", "Services"])
        return True
