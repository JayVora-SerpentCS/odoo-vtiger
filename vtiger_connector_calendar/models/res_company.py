# See LICENSE file for full copyright and licensing details.

import json
from datetime import datetime, time, timedelta
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    def _vtiger_to_bool(self, value):
        return value is True or str(value).lower() in ("1", "true", "yes", "on")

    def _parse_vtiger_date(self, value):
        if not value:
            return False
        for date_format in (DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return False

    def _parse_vtiger_time(self, value):
        if not value:
            return time()
        for time_format in ("%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"):
            try:
                return datetime.strptime(str(value).strip(), time_format).time()
            except ValueError:
                continue
        return time()

    def _prepare_vtiger_calendar_values(self, res):
        start_date = self._parse_vtiger_date(res.get("date_start"))
        end_date = self._parse_vtiger_date(res.get("due_date")) or start_date
        if not start_date:
            fallback_date = (
                self._parse_vtiger_date(res.get("createdtime"))
                or self._parse_vtiger_date(res.get("modifiedtime"))
                or fields.Date.context_today(self)
            )
            return {
                "start": fields.Datetime.to_string(
                    datetime.combine(fallback_date, time(hour=8))
                ),
                "stop": fields.Datetime.to_string(
                    datetime.combine(fallback_date, time(hour=9))
                ),
                "allday": False,
            }

        if self._vtiger_to_bool(res.get("allday")) or self._vtiger_to_bool(
            res.get("notime")
        ):
            return {
                "start": datetime.combine(start_date, time(hour=8)),
                "stop": datetime.combine(end_date, time(hour=18)),
                "start_date": start_date,
                "stop_date": end_date,
                "allday": True,
            }

        start_time = self._parse_vtiger_time(res.get("time_start"))
        end_time = self._parse_vtiger_time(res.get("time_end"))
        start_datetime = datetime.combine(start_date, start_time)
        stop_datetime = datetime.combine(end_date, end_time)

        if stop_datetime <= start_datetime:
            duration_hours = float(res.get("duration_hours") or 0.0)
            duration_minutes = float(res.get("duration_minutes") or 0.0)
            duration = timedelta(hours=duration_hours, minutes=duration_minutes)
            stop_datetime = start_datetime + (duration or timedelta(hours=1))

        return {
            "start": fields.Datetime.to_string(start_datetime),
            "stop": fields.Datetime.to_string(stop_datetime),
            "allday": False,
        }

    def _prepare_vtiger_calendar_recurrence_values(self, res):
        recurring_type = str(res.get("recurringtype") or "").strip()
        if recurring_type.lower() in ("", "--none--", "none"):
            return {}
        rrule_type = recurring_type.lower()
        if rrule_type not in dict(
            self.env["calendar.event"]._fields["rrule_type"].selection
        ):
            return {}
        return {
            "recurrency": True,
            "rrule_type": rrule_type,
        }

    def _write_vtiger_calendar_event(self, calendar_event, calendar_vals):
        recurrent_fields = calendar_event._get_recurrent_fields()
        if recurrent_fields.intersection(calendar_vals):
            calendar_vals = dict(calendar_vals, recurrence_update="all_events")
        calendar_event.with_context(
            dont_notify=True,
            no_mail_to_attendees=True,
        ).write(calendar_vals)

    def _find_existing_vtiger_calendar_event(self, res, calendar_vals):
        calendar_obj = self.env["calendar.event"]
        calendar_event = calendar_obj.search(
            [("vtiger_id", "=", res.get("id"))], limit=1
        )
        if calendar_event:
            return calendar_event
        domain = [
            ("name", "=ilike", calendar_vals.get("name")),
            ("vtiger_id", "=", False),
        ]
        if calendar_vals.get("start"):
            domain.append(("start", "=", calendar_vals["start"]))
        return calendar_obj.search(domain, limit=1)

    def action_sync_vtiger(self):
        self.sync_vtiger_calendar_event(full_sync=False)
        return super(ResCompany, self).action_sync_vtiger()

    def sync_vtiger_calendar_event(self, full_sync=True):
        calendar_obj = self.env["calendar.event"]
        for company in self:
            # Get the access key for connection
            access_key = company.get_vtiger_access_key()
            # create session
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date and not full_sync:
                qry = """SELECT * FROM Events WHERE modifiedtime >= '%s';""" % (
                    company.last_sync_date
                )
            else:
                qry = """SELECT * FROM Events;"""
            values = {"operation": "query", "query": qry, "sessionName": session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            response = urlopen(req, timeout=20)
            result = json.loads(response.read())
            if result.get("success"):
                for res in result.get("result", []):
                    calendar_vals = {
                        "name": res.get("subject"),
                    }
                    calendar_vals.update(
                        company._prepare_vtiger_calendar_recurrence_values(res)
                    )
                    calendar_vals.update(company._prepare_vtiger_calendar_values(res))
                    calendar_event = company._find_existing_vtiger_calendar_event(
                        res, calendar_vals
                    )
                    if calendar_event:
                        if not calendar_event.vtiger_id:
                            calendar_vals["vtiger_id"] = res.get("id")
                        company._write_vtiger_calendar_event(
                            calendar_event, calendar_vals
                        )
                    else:
                        calendar_vals.update(
                            {
                                "vtiger_id": res.get("id"),
                            }
                        )
                        calendar_obj.create(calendar_vals)
        return True
