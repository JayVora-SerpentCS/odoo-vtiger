# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_crm()

    def sync_vtiger_crm(self):
        crm_obj = self.env["crm.lead"]
        partner_obj = self.env["res.partner"]
        for company in self:
            # Get the access key for connection
            access_key = company.get_vtiger_access_key()
            # create session
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = """SELECT * FROM Potentials WHERE modifiedtime >= '%s';""" % (
                    company.last_sync_date
                )
            else:
                qry = """SELECT * FROM Potentials;"""

            values = {"operation": "query", "query": qry, "sessionName": session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            response = urlopen(req, timeout=20)
            result = json.loads(response.read())
            if result.get("success"):
                for res in result.get("result", []):
                    crm_vals = {
                        "name": res.get("potentialname", ""),
                        "email_from": res.get("email"),
                        "probability": float(res.get("probability")) or 0.0,
                        "date_deadline": res.get("closingdate"),
                        "expected_revenue": res.get("forecast_amount"),
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
                    crm = crm_obj.search([("vtiger_id", "=", res.get("id"))], limit=1)
                    if crm:
                        crm.write(crm_vals)
                    else:
                        crm_vals.update({"vtiger_id": res.get("id")})
                        crm_obj.create(crm_vals)
        return True
