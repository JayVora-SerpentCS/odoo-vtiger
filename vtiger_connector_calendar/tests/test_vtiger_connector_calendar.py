from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerCalendar(TransactionCase):
    def test_vtiger_calendar(self):
        # Sample Calendar Event Data
        calendar_event_vtiger_dict = {
            "success": True,
            "result": [
                {
                    "subject": "Test",
                    "assigned_user_id": "19x1",
                    "date_start": "2024-09-23",
                    "time_start": "09:30:00",
                    "due_date": "2024-09-23",
                    "time_end": "10:00:00",
                    "duration_hours": "0",
                    "duration_minutes": "30",
                    "eventstatus": "Planned",
                    "sendnotification": "0",
                    "activitytype": "Call",
                    "location": "",
                    "createdtime": "2024-09-23 09:09:00",
                    "modifiedtime": "2024-09-23 09:09:00",
                    "taskpriority": "High",
                    "notime": "0",
                    "visibility": "Public",
                    "modifiedby": "19x1",
                    "created_user_id": "19x1",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "cancellation_reason": "",
                    "allday": "0",
                    "invitation_for": "",
                    "isclosed": "0",
                    "mailing_gps_lat": "",
                    "mailing_gps_lng": "",
                    "conference_link": "",
                    "recording_link": "",
                    "event_no": "EVT316",
                    "reminder_time": "0",
                    "recurringtype": "",
                    "parent_id": "",
                    "contact_id": "",
                    "account_id": "",
                    "description": "",
                    "meeting_notes": "",
                    "checkin_datetime": "",
                    "checkout_datetime": "",
                    "checkin_duration": "",
                    "outside_geofence": "",
                    "actual_checkedin_location": "",
                    "geo_fence_violation_distance": "",
                    "id": "18x492",
                    "record_currency_symbol": None,
                }
            ],
        }
        if calendar_event_vtiger_dict.get("success"):
            calendar_result = calendar_event_vtiger_dict.get("result")[0]

            # Create User if user_id exists
            created_user_id = calendar_result.get("created_user_id")
            if created_user_id:
                self.env["res.users"].create(
                    {
                        "name": "Test user",
                        "login": "test@test",
                        "mobile": 6669998883,
                        "user_id": 1,
                    }
                )

            # Create Calendar Event
            self.env["calendar.event"].create(
                {
                    "name": calendar_result.get("subject", "Unnamed Event"),
                    "start": calendar_result.get("date_start"),
                    "stop": calendar_result.get("due_date"),
                    "recurrency": False,
                    "vtiger_id": calendar_result.get("id"),
                }
            )
