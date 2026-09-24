# See LICENSE file for full copyright and licensing details.

import re
from urllib.parse import urlencode
from urllib.request import Request

from odoo import fields, models
from odoo.tools import html2plaintext


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_pricebook_sync_date = fields.Datetime(
        string="Last VTiger Price Book Synced Time"
    )

    def action_sync_vtiger(self):
        self.sync_vtiger_pricebook(full_sync=False)
        return super().action_sync_vtiger()

    def _execute_vtiger_pricebook_query(self, company, qry, session_name):
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        return company._vtiger_request_json(req, "querying VTiger")

    def _build_vtiger_pricebook_query(self, company, full_sync=True):
        if company.last_vtiger_pricebook_sync_date and not full_sync:
            return "SELECT * FROM PriceBooks WHERE modifiedtime >= '%s';" % (
                fields.Datetime.to_string(company.last_vtiger_pricebook_sync_date)
            )
        return "SELECT * FROM PriceBooks;"

    def _is_vtiger_active(self, value):
        return str(value or "").lower() in ("1", "true", "yes", "active")

    def _clean_vtiger_html_description(self, value):
        if not value:
            return False
        text = html2plaintext(value)
        text = re.sub(r"[ \t\r\f\v]+", " ", text or "")
        text = re.sub(r" *\n *", "\n", text)
        return text.strip()

    def _prepare_vtiger_pricebook_values(self, res, company):
        return {
            "name": res.get("bookname") or res.get("pricebookname") or res.get("id"),
            "currency_id": company.currency_id.id,
            "active": self._is_vtiger_active(res.get("active", "1")),
            "vtiger_active": self._is_vtiger_active(res.get("active", "1")),
            "vtiger_description": self._clean_vtiger_html_description(
                res.get("description")
            ),
        }

    def _upsert_vtiger_pricebook(self, vals, vtiger_id):
        if not vtiger_id:
            return
        pricelist_obj = self.env["product.pricelist"]
        pricelist = pricelist_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
        if not pricelist and vals.get("name"):
            pricelist = pricelist_obj.search(
                [("name", "=ilike", vals["name"]), ("vtiger_id", "=", False)],
                limit=1,
            )
        if pricelist:
            if not pricelist.vtiger_id:
                vals["vtiger_id"] = vtiger_id
            pricelist.write(vals)
        else:
            vals["vtiger_id"] = vtiger_id
            pricelist_obj.create(vals)

    def sync_vtiger_pricebook(self, full_sync=True):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = company._build_vtiger_pricebook_query(company, full_sync=full_sync)
            result = company._execute_vtiger_pricebook_query(company, qry, session_name)
            if result.get("success"):
                for res in result.get("result", []):
                    company._upsert_vtiger_pricebook(
                        company._prepare_vtiger_pricebook_values(res, company),
                        res.get("id"),
                    )
            company.last_vtiger_pricebook_sync_date = fields.Datetime.now()
        return True
