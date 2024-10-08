# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


# Todo: Need to set tax in odoo of vtiger in product.
class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_service_products()

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
            values = {"operation": "query", "query": qry, "sessionName": session_name}

            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            response = urlopen(req, timeout=20)
            result = json.loads(response.read())
            if result.get("success"):
                product_templ_obj = self.env["product.template"]
                for res in result.get("result", []):
                    if vtiger_product_type == "Services":
                        product_vals = self.service_product_vals(res)
                    else:
                        product_vals = self.product_vals(res)
                    # Search for existing Product
                    product = product_templ_obj.search(
                        [("vtiger_id", "=", res.get("id"))], limit=1
                    )
                    if product:
                        product.write(product_vals)
                    else:
                        product_vals.update({"vtiger_id": res.get("id")})
                        product_templ_obj.create(product_vals)
        return True

    def sync_vtiger_service_products(self):
        for company in self:
            self.sync_vtiger_products(company, vtiger_type=["Products", "Services"])
        return True
