# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_partner_sync_date = fields.Datetime(
        string="Last VTiger Partner Synced Time"
    )

    def _search_existing_vtiger_partner(
        self, partner_vals, vtiger_id, is_company=False
    ):
        partner_obj = self.env["res.partner"]
        base_domain = [("is_company", "=", True)] if is_company else []

        if vtiger_id:
            partner = partner_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
            if partner:
                return partner

        for field_name in ("email", "mobile", "phone"):
            value = partner_vals.get(field_name)
            if value:
                partner = partner_obj.search(
                    base_domain
                    + [
                        (field_name, "=ilike", value),
                        ("vtiger_id", "=", False),
                    ],
                    limit=1,
                )
                if partner:
                    return partner

        if partner_vals.get("name"):
            partner = partner_obj.search(
                base_domain
                + [
                    ("name", "=ilike", partner_vals.get("name")),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
            if partner:
                return partner
        return partner_obj

    def _upsert_vtiger_partner(self, partner_vals, vtiger_id, is_company=False):
        if not vtiger_id:
            return
        partner = self._search_existing_vtiger_partner(
            partner_vals, vtiger_id, is_company=is_company
        )
        if partner:
            if is_company:
                partner_vals["is_company"] = True
            if not partner.vtiger_id:
                partner_vals["vtiger_id"] = vtiger_id
            partner.write(partner_vals)
        else:
            partner_vals.update({"vtiger_id": vtiger_id})
            if is_company:
                partner_vals["is_company"] = True
            self.env["res.partner"].create(partner_vals)

    def action_sync_vtiger(self):
        self.sync_vtiger_partner()
        return super(ResCompany, self).action_sync_vtiger()

    def _execute_vtiger_partner_query(self, company, qry, session_name):
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def contact_vals(self, res):
        name = " ".join(
            part for part in (res.get("firstname"), res.get("lastname")) if part
        )
        return {
            "name": name or res.get("email") or res.get("contact_no") or res.get("id"),
            "email": res.get("email"),
            "customer_rank": 1,
            "street": res.get("mailingstreet"),
            "city": res.get("mailingcity"),
            "zip": res.get("mailingzip"),
            "mobile": res.get("mobile"),
            "phone": res.get("phone"),
            "comment": res.get("description"),
            "country_id": res.get("mailingcountry") or False,
        }

    def vandor_vals(self, res):
        return {
            "name": res.get("vendorname") or res.get("vendor_no") or res.get("id"),
            "email": res.get("email"),
            "website": res.get("website"),
            "supplier_rank": 1,
            "street": res.get("street"),
            "city": res.get("city"),
            "zip": res.get("postalcode"),
            "mobile": res.get("mobile"),
            "phone": res.get("phone"),
            "comment": res.get("description"),
            "ref": res.get("vendor_no"),
            "country_id": res.get("country") or False,
        }

    def account_vals(self, res):
        return {
            "name": res.get("accountname") or res.get("account_no") or res.get("id"),
            "email": res.get("email1"),
            "website": res.get("website"),
            "supplier_rank": 1,
            "customer_rank": 1,
            "street": res.get("bill_street"),
            "city": res.get("bill_city"),
            "zip": res.get("bill_code"),
            "phone": res.get("phone"),
            "comment": res.get("description"),
            "country_id": res.get("bill_country") or False,
        }

    def _convert_vtiger_partner_country(self, partner_vals):
        country_value = partner_vals.get("country_id")
        if country_value:
            country = self.env["res.country"].search(
                [
                    "|",
                    ("name", "=", country_value),
                    ("code", "=", country_value),
                ],
                limit=1,
            )
            partner_vals["country_id"] = country.id if country else False
        return partner_vals

    def _sync_vtiger_partner_reference(
        self, company, vtiger_type, vtiger_id, session_name
    ):
        if not vtiger_id:
            return self.env["res.partner"]
        partner = self.env["res.partner"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if partner:
            return partner
        qry = "SELECT * FROM %s WHERE id = '%s';" % (vtiger_type, vtiger_id)
        result = company._execute_vtiger_partner_query(company, qry, session_name)
        if not result.get("success") or not result.get("result"):
            return self.env["res.partner"]
        res = result["result"][0]
        if vtiger_type == "Accounts":
            vals = company._convert_vtiger_partner_country(company.account_vals(res))
            company._upsert_vtiger_partner(vals, vtiger_id, is_company=True)
        elif vtiger_type == "Vendors":
            vals = company._convert_vtiger_partner_country(company.vandor_vals(res))
            company._upsert_vtiger_partner(vals, vtiger_id)
        else:
            vals = company._convert_vtiger_partner_country(company.contact_vals(res))
            account = company._sync_vtiger_partner_reference(
                company, "Accounts", res.get("account_id"), session_name
            )
            if account:
                vals["parent_id"] = account.id
            company._upsert_vtiger_partner(vals, vtiger_id)
        return self.env["res.partner"].search([("vtiger_id", "=", vtiger_id)], limit=1)

    def fetch_data(self, company, vtiger_type):
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        qry_template = {
            "Contacts": """SELECT * FROM Contacts WHERE modifiedtime >= '{}';""",
            "Vendors": """SELECT * FROM Vendors WHERE modifiedtime >= '{}';""",
            "Accounts": """SELECT * FROM Accounts WHERE modifiedtime >= '{}';""",
        }

        qry_template_1 = {
            "Contacts": """SELECT * FROM Contacts;""",
            "Vendors": """SELECT * FROM Vendors;""",
            "Accounts": """SELECT * FROM Accounts;""",
        }

        if company.last_vtiger_partner_sync_date:
            qry = qry_template[vtiger_type].format(
                company.last_vtiger_partner_sync_date
            )
        else:
            qry = qry_template_1[vtiger_type]
        result = company._execute_vtiger_partner_query(company, qry, session_name)
        if result.get("success"):
            for res in result.get("result", []):
                partner_vals = {}
                if vtiger_type == "Contacts":
                    partner_vals = self.contact_vals(res)
                if vtiger_type == "Vendors":
                    partner_vals = self.vandor_vals(res)
                if vtiger_type == "Accounts":
                    partner_vals = self.account_vals(res)

                if vtiger_type in ("Contacts", "Vendors", "Accounts"):
                    partner_vals = company._convert_vtiger_partner_country(partner_vals)

                    if vtiger_type == "Accounts":
                        self._upsert_vtiger_partner(
                            partner_vals, res.get("id"), is_company=True
                        )
                    else:
                        if vtiger_type == "Contacts" and res.get("account_id"):
                            account = company._sync_vtiger_partner_reference(
                                company, "Accounts", res.get("account_id"), session_name
                            )
                            if account:
                                partner_vals["parent_id"] = account.id
                        self._upsert_vtiger_partner(partner_vals, res.get("id"))
        return True

    def sync_vtiger_partner(self):
        for company in self:
            company.fetch_data(company, vtiger_type="Contacts")
            company.fetch_data(company, vtiger_type="Vendors")
            company.fetch_data(company, vtiger_type="Accounts")
            company.last_vtiger_partner_sync_date = fields.Datetime.now()
        return True

    def sync_vtiger_partner_vendor(self):
        for company in self:
            self.fetch_data(company, vtiger_type="Vendors")
        return True

    def sync_vtiger_partner_organizations(self):
        for company in self:
            self.fetch_data(company, vtiger_type="Accounts")
        return True
