# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_crm_sync_date = fields.Datetime(string="Last VTiger CRM Synced Time")

    def _vtiger_float(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def action_sync_vtiger(self):
        self.sync_vtiger_crm()
        return super(ResCompany, self).action_sync_vtiger()

    def _get_vtiger_records(self, company, vtiger_type):
        query_by_type = {
            "Leads": "SELECT * FROM Leads WHERE modifiedtime >= '%s';",
            "Potentials": "SELECT * FROM Potentials WHERE modifiedtime >= '%s';",
        }
        full_query_by_type = {
            "Leads": "SELECT * FROM Leads;",
            "Potentials": "SELECT * FROM Potentials;",
        }
        if company.last_vtiger_crm_sync_date:
            qry = query_by_type[vtiger_type] % company.last_vtiger_crm_sync_date
        else:
            qry = full_query_by_type[vtiger_type]

        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        result = json.loads(response.read())
        if result.get("success"):
            return result.get("result", [])
        return []

    def _prepare_vtiger_lead_values(self, res):
        contact_name = " ".join(
            part for part in (res.get("firstname"), res.get("lastname")) if part
        )
        lead_name = (
            contact_name or res.get("company") or res.get("lead_no") or res.get("id")
        )
        country = self.env["res.country"].search(
            [
                "|",
                ("name", "=", res.get("country")),
                ("code", "=", res.get("country")),
            ],
            limit=1,
        )
        return {
            "type": "lead",
            "name": lead_name or "",
            "contact_name": contact_name,
            "partner_name": res.get("company"),
            "email_from": res.get("email"),
            "phone": res.get("phone"),
            "mobile": res.get("mobile"),
            "website": res.get("website"),
            "street": res.get("lane"),
            "city": res.get("city"),
            "zip": res.get("code"),
            "country_id": country.id if country else False,
            "description": res.get("description"),
        }

    def _prepare_vtiger_potential_values(self, res, partner_obj):
        crm_vals = {
            "type": "opportunity",
            "name": res.get("potentialname", ""),
            "email_from": res.get("email"),
            "probability": self._vtiger_float(res.get("probability")),
            "date_deadline": res.get("closingdate"),
            "expected_revenue": self._vtiger_float(res.get("forecast_amount")),
            "description": res.get("description"),
            "activity_summary": res.get("nextstep"),
            "priority": res.get("starred", ""),
        }
        if res.get("contact_id"):
            partner_exist = partner_obj.search(
                [("vtiger_id", "=", res.get("contact_id"))], limit=1
            )
            if partner_exist:
                crm_vals.update({"partner_id": partner_exist.id})
        return crm_vals

    def _upsert_vtiger_crm(self, crm_vals, vtiger_id):
        if not vtiger_id:
            return
        crm_obj = self.env["crm.lead"]
        crm = crm_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
        if not crm:
            crm_type = crm_vals.get("type") or "lead"
            for field_name in ("email_from", "phone", "mobile"):
                value = crm_vals.get(field_name)
                if value:
                    crm = crm_obj.search(
                        [
                            ("type", "=", crm_type),
                            (field_name, "=ilike", value),
                            ("vtiger_id", "=", False),
                        ],
                        limit=1,
                    )
                    if crm:
                        break
        if not crm and crm_vals.get("name"):
            crm = crm_obj.search(
                [
                    ("type", "=", crm_vals.get("type") or "lead"),
                    ("name", "=ilike", crm_vals.get("name")),
                    ("vtiger_id", "=", False),
                ],
                limit=1,
            )
        if crm:
            if not crm.vtiger_id:
                crm_vals["vtiger_id"] = vtiger_id
            crm.write(crm_vals)
        else:
            crm_vals.update({"vtiger_id": vtiger_id})
            crm_obj.create(crm_vals)

    def sync_vtiger_crm(self):
        partner_obj = self.env["res.partner"]
        for company in self:
            for res in company._get_vtiger_records(company, "Leads"):
                company._upsert_vtiger_crm(
                    company._prepare_vtiger_lead_values(res), res.get("id")
                )
            for res in company._get_vtiger_records(company, "Potentials"):
                company._upsert_vtiger_crm(
                    company._prepare_vtiger_potential_values(res, partner_obj),
                    res.get("id"),
                )
            company.last_vtiger_crm_sync_date = fields.Datetime.now()
        return True
