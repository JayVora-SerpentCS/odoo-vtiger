# See LICENSE file for full copyright and licensing details.

from datetime import datetime, time, timedelta
from urllib.parse import urlencode
from urllib.request import Request

from odoo import Command, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    last_vtiger_calendar_sync_date = fields.Datetime(
        string="Last VTiger Calendar Synced Time"
    )

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

    def _default_vtiger_calendar_user(self):
        user = self.env.user
        if not user.partner_id:
            user = self.env.ref("base.user_admin", raise_if_not_found=False) or user
        return user

    def _add_vtiger_calendar_attendee_values(self, vals, user):
        vals["user_id"] = user.id
        if user.partner_id:
            vals["partner_ids"] = [Command.link(user.partner_id.id)]
        return vals

    def _prepare_vtiger_calendar_values(self, res):
        user = self._default_vtiger_calendar_user()
        start_date = self._parse_vtiger_date(res.get("date_start"))
        end_date = self._parse_vtiger_date(res.get("due_date")) or start_date
        if not start_date:
            fallback_date = (
                self._parse_vtiger_date(res.get("createdtime"))
                or self._parse_vtiger_date(res.get("modifiedtime"))
                or fields.Date.context_today(self)
            )
            start_datetime = datetime.combine(fallback_date, time(hour=8))
            stop_datetime = datetime.combine(fallback_date, time(hour=9))
            return self._add_vtiger_calendar_attendee_values(
                {
                    "start": fields.Datetime.to_string(start_datetime),
                    "stop": fields.Datetime.to_string(stop_datetime),
                    "duration": 1.0,
                    "allday": False,
                },
                user,
            )

        if self._vtiger_to_bool(res.get("allday")) or self._vtiger_to_bool(
            res.get("notime")
        ):
            start_datetime = datetime.combine(start_date, time(hour=8))
            stop_datetime = datetime.combine(end_date, time(hour=18))
            return self._add_vtiger_calendar_attendee_values(
                {
                    "start": fields.Datetime.to_string(start_datetime),
                    "stop": fields.Datetime.to_string(stop_datetime),
                    "start_date": start_date,
                    "stop_date": end_date,
                    "duration": max(
                        (stop_datetime - start_datetime).total_seconds() / 3600, 1.0
                    ),
                    "allday": True,
                },
                user,
            )

        start_time = self._parse_vtiger_time(res.get("time_start"))
        end_time = self._parse_vtiger_time(res.get("time_end"))
        start_datetime = datetime.combine(start_date, start_time)
        stop_datetime = datetime.combine(end_date, end_time)

        if stop_datetime <= start_datetime:
            duration_hours = float(res.get("duration_hours") or 0.0)
            duration_minutes = float(res.get("duration_minutes") or 0.0)
            duration = timedelta(hours=duration_hours, minutes=duration_minutes)
            stop_datetime = start_datetime + (duration or timedelta(hours=1))

        return self._add_vtiger_calendar_attendee_values(
            {
                "start": fields.Datetime.to_string(start_datetime),
                "stop": fields.Datetime.to_string(stop_datetime),
                "duration": (stop_datetime - start_datetime).total_seconds() / 3600,
                "allday": False,
            },
            user,
        )

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
        super().action_sync_vtiger()
        return {"type": "ir.actions.client", "tag": "reload"}

    def sync_vtiger_calendar_event(self, full_sync=True):
        calendar_obj = self.env["calendar.event"]
        for company in self:
            # Get the access key for connection
            access_key = company.get_vtiger_access_key()
            # create session
            session_name = company.vtiger_login(access_key)
            if company.last_vtiger_calendar_sync_date and not full_sync:
                qry = """SELECT * FROM Events WHERE modifiedtime >= '%s';""" % (
                    fields.Datetime.to_string(company.last_vtiger_calendar_sync_date)
                )
            else:
                qry = """SELECT * FROM Events;"""
            values = {"operation": "query", "query": qry, "sessionName": session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            result = company._vtiger_request_json(req, "querying VTiger")
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
            company.last_vtiger_calendar_sync_date = fields.Datetime.now()
        return True
