# See LICENSE file for full copyright and licensing details.

import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        self.sync_vtiger_project_task()
        return super(ResCompany, self).action_sync_vtiger()

    def _execute_vtiger_project_query(self, company, qry, session_name=False):
        if not session_name:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _build_vtiger_project_query(self, vtiger_module, company):
        if company.last_sync_date:
            return "SELECT * FROM %s WHERE modifiedtime >= '%s';" % (
                vtiger_module,
                company.last_sync_date,
            )
        return "SELECT * FROM %s;" % vtiger_module

    def _get_vtiger_query_records(self, company, queries, session_name=False):
        for qry in queries:
            result = self._execute_vtiger_project_query(company, qry, session_name)
            if result.get("success") and result.get("result"):
                return result.get("result", [])
        return []

    def _safe_float(self, value):
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    def _get_task_allocated_hours(self, res):
        if res.get("estimated_hours"):
            return self._safe_float(res.get("estimated_hours"))
        if res.get("duration_hours") or res.get("duration_minutes"):
            return self._safe_float(res.get("duration_hours")) + (
                self._safe_float(res.get("duration_minutes")) / 60.0
            )
        estimate = str(res.get("estimate") or "").lower()
        if "min" in estimate:
            return self._safe_float(estimate.split()[0]) / 60.0
        return self._safe_float(res.get("estimate"))

    def _get_vtiger_partner(self, company, vtiger_id):
        if not vtiger_id:
            return self.env["res.partner"]
        partner = self.env["res.partner"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if partner:
            return partner
        company.sync_vtiger_partner()
        return self.env["res.partner"].search([("vtiger_id", "=", vtiger_id)], limit=1)

    def _get_vtiger_project(self, company, vtiger_id):
        if not vtiger_id:
            return self.env["project.project"]
        project = self.env["project.project"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )
        if project:
            return project
        if "x" not in str(vtiger_id):
            project = self.env["project.project"].search(
                [("name", "=ilike", vtiger_id)], limit=1
            )
            if project:
                return project
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        qry = "SELECT * FROM Project WHERE id = '%s';" % vtiger_id
        result = self._execute_vtiger_project_query(company, qry, session_name)
        if result.get("success") and result.get("result"):
            vtiger_project = result["result"][0]
            self._upsert_vtiger_project(
                self._prepare_vtiger_project_values(vtiger_project, company),
                vtiger_project.get("id"),
            )
        return self.env["project.project"].search(
            [("vtiger_id", "=", vtiger_id)], limit=1
        )

    def _get_task_project(self, company, res):
        for field_name in (
            "projectid",
            "project_id",
            "project",
            "projectname",
            "project_name",
            "projecttaskid",
            "linktoproject",
            "related_project",
            "parent_id",
            "related_to",
            "parentid",
            "linktoaccountscontacts",
        ):
            project_value = res.get(field_name)
            project = self._get_vtiger_project(company, project_value)
            if project:
                return project

        for field_name in (
            "projectid_display",
            "project_id_display",
            "projectname_display",
            "project_name_display",
            "projectid_label",
            "project_id_label",
        ):
            project_name = res.get(field_name)
            if project_name:
                project = self.env["project.project"].search(
                    [("name", "=ilike", project_name)], limit=1
                )
                if project:
                    return project
        return self.env["project.project"]

    def _get_vtiger_user(self, vtiger_id):
        if not vtiger_id or "vtiger_id" not in self.env["res.users"]._fields:
            return self.env["res.users"]
        return self.env["res.users"].search([("vtiger_id", "=", vtiger_id)], limit=1)

    def _get_task_stage(self, stage_name, project):
        if not stage_name:
            return self.env["project.task.type"]
        stage_domain = [("name", "=ilike", stage_name)]
        if project:
            stage_domain = [
                ("name", "=ilike", stage_name),
                "|",
                ("project_ids", "=", False),
                ("project_ids", "in", project.ids),
            ]
        stage = self.env["project.task.type"].search(stage_domain, limit=1)
        if stage:
            return stage
        stage_vals = {"name": stage_name}
        if project:
            stage_vals["project_ids"] = [(4, project.id)]
        return self.env["project.task.type"].create(stage_vals)

    def _prepare_vtiger_project_values(self, res, company):
        project_vals = {
            "name": res.get("projectname") or res.get("project_no") or res.get("id"),
        }
        contact_id = res.get("linktoaccountscontacts") or res.get("contactid")
        try:
            partner = self._get_vtiger_partner(company, contact_id)
        except Exception:
            _logger.exception(
                "Failed to resolve VTiger partner %s for project %s",
                contact_id,
                res.get("id"),
            )
            partner = self.env["res.partner"]
        if partner:
            project_vals.update({"partner_id": partner.id})
        return project_vals

    def _prepare_vtiger_task_values(self, res, company):
        project = self._get_task_project(company, res)
        partner = self.env["res.partner"]
        for vtiger_partner_id in (
            res.get("contact_id"),
            res.get("parent_id"),
            res.get("related_to"),
            res.get("account_id"),
        ):
            try:
                partner = self._get_vtiger_partner(company, vtiger_partner_id)
            except Exception:
                _logger.exception(
                    "Failed to resolve VTiger partner %s for task %s",
                    vtiger_partner_id,
                    res.get("id"),
                )
                partner = self.env["res.partner"]
            if partner:
                break

        task_vals = {
            "name": res.get("subject") or res.get("taskname") or res.get("id"),
            "description": res.get("description"),
            "priority": "1"
            if str(res.get("taskpriority", "")).lower() == "high"
            else "0",
            "allocated_hours": self._get_task_allocated_hours(res),
        }
        if not task_vals["name"] and res.get("label"):
            task_vals["name"] = res.get("label")
        if project:
            task_vals["project_id"] = project.id
        if partner:
            task_vals["partner_id"] = partner.id
        due_date = res.get("due_date") or res.get("due_date_time")
        if due_date:
            task_vals["date_deadline"] = due_date

        stage = self._get_task_stage(res.get("taskstatus"), project)
        if stage:
            task_vals["stage_id"] = stage.id
        if str(res.get("taskstatus", "")).lower() in ("completed", "closed", "done"):
            task_vals["state"] = "1_done"
        else:
            task_vals["state"] = "01_in_progress"

        user = self._get_vtiger_user(res.get("assigned_user_id"))
        if user:
            task_vals["user_ids"] = [(6, 0, user.ids)]

        parent_task = self.env["project.task"].search(
            [("vtiger_id", "=", res.get("parent_task_id"))], limit=1
        )
        if parent_task:
            task_vals["parent_id"] = parent_task.id
        return task_vals

    def _upsert_vtiger_project(self, project_vals, vtiger_id):
        if not vtiger_id:
            return
        project_obj = self.env["project.project"]
        project = project_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
        if not project and project_vals.get("name"):
            project = project_obj.search(
                [("name", "=ilike", project_vals["name"]), ("vtiger_id", "=", False)],
                limit=1,
            )
        if project:
            if not project.vtiger_id:
                project_vals["vtiger_id"] = vtiger_id
            project.write(project_vals)
        else:
            project_vals.update({"vtiger_id": vtiger_id})
            project_obj.create(project_vals)

    def _upsert_vtiger_task(self, task_vals, vtiger_id):
        if not vtiger_id:
            return
        task_obj = self.env["project.task"]
        task = task_obj.search([("vtiger_id", "=", vtiger_id)], limit=1)
        if not task and task_vals.get("name"):
            task_domain = [
                ("name", "=ilike", task_vals["name"]),
                ("vtiger_id", "=", False),
            ]
            if task_vals.get("project_id"):
                task_domain.append(("project_id", "=", task_vals["project_id"]))
            task = task_obj.search(task_domain, limit=1)
        if task:
            if not task.vtiger_id:
                task_vals["vtiger_id"] = vtiger_id
            task.write(task_vals)
        else:
            task_vals.update({"vtiger_id": vtiger_id})
            task_obj.create(task_vals)

    def sync_vtiger_project(self, full_sync=False):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = (
                "SELECT * FROM Project;"
                if full_sync
                else self._build_vtiger_project_query("Project", company)
            )
            records = self._get_vtiger_query_records(company, [qry], session_name)
            for res in records:
                try:
                    self._upsert_vtiger_project(
                        self._prepare_vtiger_project_values(res, company),
                        res.get("id"),
                    )
                except Exception:
                    _logger.exception("Failed to sync VTiger project %s", res.get("id"))
        return True

    def sync_vtiger_task(self, full_sync=False):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if full_sync:
                queries = [
                    "SELECT * FROM Tasks;",
                    "SELECT * FROM Calendar WHERE activitytype = 'Task';",
                    "SELECT * FROM Calendar;",
                    "SELECT * FROM ProjectTask;",
                ]
            else:
                queries = [
                    self._build_vtiger_project_query("Tasks", company),
                    (
                        "SELECT * FROM Calendar WHERE modifiedtime >= '%s' "
                        "AND activitytype = 'Task';"
                    )
                    % company.last_sync_date
                    if company.last_sync_date
                    else "SELECT * FROM Calendar WHERE activitytype = 'Task';",
                    self._build_vtiger_project_query("ProjectTask", company),
                ]
            records = self._get_vtiger_query_records(company, queries, session_name)
            for res in records:
                if res.get("activitytype") and res.get("activitytype") != "Task":
                    continue
                try:
                    self._upsert_vtiger_task(
                        self._prepare_vtiger_task_values(res, company),
                        res.get("id"),
                    )
                except Exception:
                    _logger.exception("Failed to sync VTiger task %s", res.get("id"))
        return True

    def sync_vtiger_project_task(self):
        self.sync_vtiger_project(full_sync=True)
        self.sync_vtiger_task(full_sync=True)
        return True
