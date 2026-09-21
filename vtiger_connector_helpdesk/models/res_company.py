# See LICENSE file for full copyright and licensing details.

import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_helpdesk_sync_date = fields.Datetime(
        string="Last VTiger HelpDesk Synced Time"
    )

    def action_sync_vtiger(self):
        self.sync_vtiger_helpdesk_ticket(full_sync=False)
        return super(ResCompany, self).action_sync_vtiger()

    def _execute_vtiger_helpdesk_query(self, company, qry, session_name):
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _execute_vtiger_retrieve(self, company, vtiger_id, session_name):
        if not vtiger_id or "x" not in str(vtiger_id):
            return {}
        values = {
            "operation": "retrieve",
            "id": vtiger_id,
            "sessionName": session_name,
        }
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        result = json.loads(response.read())
        if result.get("success"):
            return result.get("result", {})
        _logger.warning("VTiger retrieve failed for %s: %s", vtiger_id, result)
        return {}

    def _build_vtiger_helpdesk_query(self, vtiger_module, company):
        if company.last_vtiger_helpdesk_sync_date:
            return "SELECT * FROM %s WHERE modifiedtime >= '%s';" % (
                vtiger_module,
                company.last_vtiger_helpdesk_sync_date,
            )
        return "SELECT * FROM %s;" % vtiger_module

    def _get_vtiger_helpdesk_records(self, company, queries, session_name):
        records = []
        for qry in queries:
            try:
                result = company._execute_vtiger_helpdesk_query(
                    company, qry, session_name
                )
            except Exception:
                _logger.exception("Failed to execute VTiger HelpDesk query: %s", qry)
                continue
            if result.get("success"):
                records += result.get("result", [])
                continue
            _logger.warning("VTiger HelpDesk query failed: %s", result)
        return records

    def _get_vtiger_partner(self, company, vtiger_id, session_name=False, create=False):
        if not vtiger_id:
            return self.env["res.partner"]
        if "x" not in str(vtiger_id):
            return self._get_vtiger_partner_by_name(vtiger_id, create=create)
        partner = self.env["res.partner"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if partner:
            return partner
        company.sync_vtiger_partner()
        partner = self.env["res.partner"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if partner or not create or not session_name:
            return partner
        return self._create_vtiger_partner_from_reference(
            company, vtiger_id, session_name
        )

    def _get_vtiger_partner_by_name(self, partner_name, create=False):
        if not partner_name:
            return self.env["res.partner"]
        partner = self.env["res.partner"].search(
            [("name", "=ilike", partner_name)], limit=1
        )
        if partner or not create:
            return partner
        return self.env["res.partner"].create(
            {"name": partner_name, "customer_rank": 1}
        )

    def _create_vtiger_partner_from_reference(self, company, vtiger_id, session_name):
        res = self._execute_vtiger_retrieve(company, vtiger_id, session_name)
        if not res:
            return self.env["res.partner"]
        name = (
            " ".join(
                part for part in (res.get("firstname"), res.get("lastname")) if part
            )
            or res.get("accountname")
            or res.get("contactname")
            or res.get("lastname")
            or res.get("label")
            or vtiger_id
        )
        vals = {
            "name": name,
            "email": res.get("email") or res.get("email1"),
            "phone": res.get("phone"),
            "mobile": res.get("mobile"),
            "customer_rank": 1,
            "vtiger_id": vtiger_id,
        }
        return self.env["res.partner"].create(
            {key: value for key, value in vals.items() if value}
        )

    def _get_vtiger_user(
        self,
        company,
        vtiger_user_id=False,
        user_name=False,
        session_name=False,
        create=False,
    ):
        user_obj = self.env["res.users"].with_context(
            active_test=False, no_reset_password=True
        )
        user = user_obj
        if vtiger_user_id and "vtiger_id" in user_obj._fields:
            user = user_obj.search([("vtiger_id", "=", vtiger_user_id)], limit=1)
        vtiger_user_vals = {}
        if not user and vtiger_user_id and "x" in str(vtiger_user_id) and session_name:
            vtiger_user_vals = self._execute_vtiger_retrieve(
                company, vtiger_user_id, session_name
            )
            user_name = user_name or self._get_vtiger_user_name(vtiger_user_vals)
            user_email = vtiger_user_vals.get("email1") or vtiger_user_vals.get("email")
            if user_email:
                user = user_obj.search([("login", "=", user_email)], limit=1)
        if not user and vtiger_user_id and "x" not in str(vtiger_user_id):
            user = user_obj.search([("name", "=ilike", vtiger_user_id)], limit=1)
            if not user and not user_name:
                user_name = vtiger_user_id
        if not user and user_name:
            user = user_obj.search([("name", "=ilike", user_name)], limit=1)
        if user or not create or not user_name:
            return user
        user_vals = {
            "name": user_name,
            "login": (
                vtiger_user_vals.get("email1")
                or vtiger_user_vals.get("email")
                or self._get_vtiger_user_login(user_name, vtiger_user_id)
            ),
        }
        if (
            vtiger_user_id
            and "vtiger_id" in user_obj._fields
            and "x" in str(vtiger_user_id)
        ):
            user_vals["vtiger_id"] = vtiger_user_id
        return user_obj.create(user_vals)

    def _get_vtiger_user_name(self, user_vals):
        return (
            " ".join(
                part
                for part in (
                    user_vals.get("first_name") or user_vals.get("firstname"),
                    user_vals.get("last_name") or user_vals.get("lastname"),
                )
                if part
            )
            or user_vals.get("user_name")
            or user_vals.get("label")
        )

    def _get_vtiger_user_login(self, user_name, vtiger_user_id=False):
        login_base = str(user_name or vtiger_user_id or "vtiger_user").strip()
        login_base = login_base.lower().replace(" ", ".")
        login = "%s@vtiger" % login_base
        counter = 1
        user_obj = self.env["res.users"]
        while user_obj.search([("login", "=", login)], limit=1):
            counter += 1
            login = "%s.%s@vtiger" % (login_base, counter)
        return login

    def _get_partner_phone(self, partner):
        if not partner:
            return False
        return partner.phone or partner.mobile

    def _get_vtiger_helpdesk_team(self):
        ticket_obj = self.env["helpdesk.ticket"]
        default_team_id = ticket_obj.default_get(["team_id"]).get("team_id")
        if default_team_id:
            return self.env["helpdesk.team"].browse(default_team_id)
        return self.env["helpdesk.team"].search([], limit=1)

    def _get_vtiger_helpdesk_stage(self, stage_name, team=False):
        if not stage_name:
            return self.env["helpdesk.stage"]
        stage_name = self._map_vtiger_helpdesk_stage_name(stage_name)
        stage_obj = self.env["helpdesk.stage"]
        domain = [("name", "=ilike", stage_name)]
        if team and "team_ids" in stage_obj._fields:
            domain = [
                ("name", "=ilike", stage_name),
                "|",
                ("team_ids", "=", False),
                ("team_ids", "in", team.ids),
            ]
        stage = stage_obj.search(domain, limit=1)
        if stage:
            return stage
        return stage_obj.search([("name", "=ilike", stage_name)], limit=1)

    def _map_vtiger_helpdesk_stage_name(self, stage_name):
        stage = str(stage_name or "").strip().lower()
        stage_map = {
            "in planning": "In Progress",
            "planned": "In Progress",
            "planning": "In Progress",
            "active": "In Progress",
            "open": "New",
            "new": "New",
            "on hold": "On Hold",
            "hold": "On Hold",
            "complete": "Solved",
            "completed": "Solved",
            "closed": "Solved",
            "done": "Solved",
            "archived": "Solved",
            "cancelled": "Cancelled",
            "canceled": "Cancelled",
        }
        return stage_map.get(stage, stage_name)

    def _prepare_vtiger_helpdesk_values(self, res, company):
        partner = self._get_vtiger_partner(company, res.get("parent_id"))
        contact = self._get_vtiger_partner(company, res.get("contact_id"))
        team = self._get_vtiger_helpdesk_team()
        vals = {
            "name": res.get("ticket_title") or res.get("title") or res.get("id"),
            "vtiger_source_module": "HelpDesk",
            "vtiger_ticket_no": res.get("ticket_no"),
            "partner_id": partner.id if partner else False,
            "partner_name": contact.name if contact else False,
            "partner_email": contact.email if contact else False,
            "partner_phone": contact.phone if contact else False,
            "vtiger_status": res.get("ticketstatus"),
            "priority": self._map_vtiger_ticket_priority(res.get("ticketpriorities")),
            "vtiger_category": res.get("ticketcategories"),
            "vtiger_severity": res.get("severity"),
            "description": res.get("description"),
            "vtiger_solution": res.get("solution"),
            "vtiger_createdtime": self._to_vtiger_datetime(res.get("createdtime")),
            "vtiger_modifiedtime": self._to_vtiger_datetime(res.get("modifiedtime")),
        }
        if team:
            vals["team_id"] = team.id
        stage = self._get_vtiger_helpdesk_stage(res.get("ticketstatus"), team)
        if stage:
            vals["stage_id"] = stage.id
        return vals

    def _get_first_vtiger_value(self, res, field_names):
        for field_name in field_names:
            value = res.get(field_name)
            if value not in (False, None, ""):
                return value
        return False

    def _get_vtiger_service_contract_partner(self, company, res, session_name):
        for field_names in (
            ("sc_related_to", "sc_relatedto", "related_to", "relatedto"),
            ("parent_id", "account_id", "accountid"),
            ("contact_id", "contactid", "contactname", "contact_id_display"),
        ):
            partner_value = self._get_first_vtiger_value(res, field_names)
            partner = self._get_vtiger_partner(
                company, partner_value, session_name=session_name, create=True
            )
            if partner:
                return partner
        return self._get_vtiger_partner_by_name(
            self._get_first_vtiger_value(
                res,
                (
                    "contact_id_label",
                    "contactname_label",
                    "contact_name",
                    "contact",
                    "parent_id_label",
                    "related_to_label",
                    "sc_related_to_label",
                    "sc_relatedto_label",
                    "accountname",
                    "account_name",
                ),
            ),
            create=True,
        )

    def _prepare_vtiger_service_contract_values(self, res, company, session_name):
        partner = self._get_vtiger_service_contract_partner(company, res, session_name)
        contact = self._get_vtiger_partner(
            company,
            self._get_first_vtiger_value(
                res, ("contact_id", "contactid", "contactname")
            ),
            session_name=session_name,
            create=True,
        )
        contact_value = self._get_first_vtiger_value(
            res, ("contact_id", "contactid", "contactname")
        )
        if not contact and contact_value and "x" not in str(contact_value):
            contact = self._get_vtiger_partner_by_name(contact_value, create=True)
        if not contact:
            contact = self._get_vtiger_partner_by_name(
                self._get_first_vtiger_value(
                    res,
                    (
                        "contact_id_label",
                        "contactid_label",
                        "contactname_label",
                        "contact_name",
                    ),
                ),
                create=True,
            )
        team = self._get_vtiger_helpdesk_team()
        subject = self._get_first_vtiger_value(
            res,
            (
                "subject",
                "contract_no",
                "servicecontract_no",
                "servicecontracts_no",
                "contract_name",
                "id",
            ),
        )
        status = self._get_first_vtiger_value(
            res, ("contract_status", "servicestatus", "status")
        )
        description = self._prepare_service_contract_description(res)
        ticket_partner = contact or partner
        vals = {
            "name": subject,
            "vtiger_source_module": "ServiceContracts",
            "vtiger_ticket_no": self._get_first_vtiger_value(
                res,
                (
                    "contract_no",
                    "servicecontract_no",
                    "servicecontracts_no",
                    "servicecontractid",
                ),
            ),
            "vtiger_status": status,
            "priority": self._map_vtiger_ticket_priority(
                self._get_first_vtiger_value(
                    res, ("priority", "contract_priority", "service_priority")
                )
            ),
            "vtiger_category": self._get_first_vtiger_value(
                res, ("contract_type", "contracttype", "type")
            ),
            "description": description,
            "vtiger_solution": res.get("description"),
            "vtiger_createdtime": self._to_vtiger_datetime(res.get("createdtime")),
            "vtiger_modifiedtime": self._to_vtiger_datetime(res.get("modifiedtime")),
        }
        if ticket_partner:
            vals.update(
                {
                    "partner_id": ticket_partner.id,
                    "partner_name": ticket_partner.name,
                    "partner_email": ticket_partner.email,
                    "partner_phone": self._get_partner_phone(ticket_partner),
                }
            )
        if team:
            vals["team_id"] = team.id
        stage = self._get_vtiger_helpdesk_stage(vals.get("vtiger_status"), team)
        if stage:
            vals["stage_id"] = stage.id
        user = self._get_vtiger_user(
            company,
            self._get_first_vtiger_value(res, ("assigned_user_id", "smownerid")),
            self._get_first_vtiger_value(
                res,
                (
                    "assigned_user_id_label",
                    "assigned_to",
                    "assigned_user_name",
                    "smownerid_label",
                ),
            ),
            session_name=session_name,
            create=True,
        )
        if user:
            vals["user_id"] = user.id
        if str(status or "").strip().lower() in ("completed", "closed", "done"):
            vals["kanban_state"] = "done"
        return vals

    def _prepare_service_contract_description(self, res):
        lines = []
        description = res.get("description")
        if description:
            lines.append(description)
            lines.append("")
        for label, field_names in (
            ("Subject", ("subject",)),
            ("Type", ("contract_type", "contracttype", "type")),
            ("Status", ("contract_status", "servicestatus", "status")),
            ("Priority", ("priority", "contract_priority", "service_priority")),
            (
                "Assigned To",
                ("assigned_user_id_label", "assigned_to", "assigned_user_name"),
            ),
            (
                "Customer",
                (
                    "contact_id_label",
                    "contactname_label",
                    "contact_name",
                    "parent_id_label",
                    "related_to_label",
                    "accountname",
                    "account_name",
                ),
            ),
            ("Tracking Unit", ("tracking_unit", "trackingunit")),
            ("Total Units", ("total_units", "totalunits")),
            ("Used Units", ("used_units", "usedunits")),
            ("Remaining Units", ("remaining_units", "remainingunits")),
            ("Start Date", ("start_date", "contract_start_date", "startdate")),
            ("End Date", ("end_date", "contract_end_date", "enddate", "due_date")),
        ):
            value = self._get_first_vtiger_value(res, field_names)
            if value:
                lines.append("%s: %s" % (label, value))
        return "\n".join(lines)

    def _get_vtiger_record_key(self, vtiger_module, vtiger_id):
        if not vtiger_id:
            return False
        return "%s:%s" % (vtiger_module, vtiger_id)

    def _to_vtiger_datetime(self, value):
        return fields.Datetime.to_datetime(value) if value else False

    def _vtiger_float(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _map_vtiger_ticket_priority(self, value):
        priority = str(value or "").strip().lower()
        if priority in ("urgent", "critical"):
            return "3"
        if priority == "high":
            return "2"
        if priority in ("medium", "normal"):
            return "1"
        return "0"

    def _upsert_vtiger_helpdesk_ticket(self, vals, vtiger_id, vtiger_module):
        if not vtiger_id:
            return
        vtiger_key = self._get_vtiger_record_key(vtiger_module, vtiger_id)
        ticket_obj = self.env["helpdesk.ticket"]
        ticket = ticket_obj.search([("vtiger_id", "=", vtiger_key)], limit=1)
        if not ticket:
            ticket = ticket_obj.search(
                [
                    ("vtiger_id", "=", vtiger_id),
                    ("vtiger_source_module", "in", [False, vtiger_module]),
                ],
                limit=1,
            )
        vals["vtiger_id"] = vtiger_key
        if ticket:
            ticket.write(vals)
        else:
            ticket_obj.create(vals)

    def sync_vtiger_helpdesk_ticket(self, full_sync=True):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            helpdesk_query = (
                "SELECT * FROM HelpDesk;"
                if full_sync
                else company._build_vtiger_helpdesk_query("HelpDesk", company)
            )
            service_contract_queries = (
                ["SELECT * FROM ServiceContracts;"]
                if full_sync
                else [company._build_vtiger_helpdesk_query("ServiceContracts", company)]
            )
            helpdesk_records = company._get_vtiger_helpdesk_records(
                company,
                [helpdesk_query],
                session_name,
            )
            service_contract_records = company._get_vtiger_helpdesk_records(
                company,
                service_contract_queries,
                session_name,
            )
            for res in helpdesk_records:
                try:
                    company._upsert_vtiger_helpdesk_ticket(
                        company._prepare_vtiger_helpdesk_values(res, company),
                        res.get("id"),
                        "HelpDesk",
                    )
                except Exception:
                    _logger.exception(
                        "Failed to sync VTiger HelpDesk ticket %s", res.get("id")
                    )
            for res in service_contract_records:
                try:
                    company._upsert_vtiger_helpdesk_ticket(
                        company._prepare_vtiger_service_contract_values(
                            res, company, session_name
                        ),
                        res.get("id"),
                        "ServiceContracts",
                    )
                except Exception:
                    _logger.exception(
                        "Failed to sync VTiger service contract %s", res.get("id")
                    )
            company.last_vtiger_helpdesk_sync_date = fields.Datetime.now()
        return True
