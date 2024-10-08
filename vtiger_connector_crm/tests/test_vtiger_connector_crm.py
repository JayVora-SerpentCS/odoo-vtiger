from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerCrm(TransactionCase):
    def test_vtiger_crm(self):
        # Sample CRM data
        crm_vtiger_dict = {
            "success": True,
            "result": [
                {
                    "potentialname": "Test deal",
                    "amount_currency_value": "500.00000000",
                    "amount": "500.00000000",
                    "related_to": "",
                    "contact_id": "4x494",
                    "closingdate": "2024-09-30",
                    "pipeline": "Standard",
                    "sales_stage": "New",
                    "assigned_user_id": "19x1",
                    "leadsource": "Cold Call",
                    "nextstep": "",
                    "opportunity_type": "Existing Business",
                    "probability": "5.000",
                    "modifiedby": "19x1",
                    "forecast_amount_currency_value": "25.00000000",
                    "forecast_amount": "25.00000000",
                    "createdtime": "2024-09-27 08:22:52",
                    "modifiedtime": "2024-09-27 08:24:12",
                    "potential_no": "POT15",
                    "isconvertedfromlead": "0",
                    "created_user_id": "19x1",
                    "forecast_category": "Pipeline",
                    "adjusted_amount": "500.00000000",
                    "adjusted_amount_currency_value": "500.00000000",
                    "source": "CRM",
                    "last_contacted_on": "2024-09-27 08:24:15",
                    "last_contacted_via": "Emails",
                    "starred": "0",
                    "tags": "",
                    "current_stage_entry_time": "2024-09-27 08:22:52",
                    "lost_reason": "",
                    "record_currency_id": "21x2",
                    "record_conversion_rate": "1.00000",
                    "journey_template_id": "53x257",
                    "next_journey": "",
                    "progress": "0.00",
                    "opp_contactrole": "",
                    "isclosed": "0",
                    "prev_sales_stage": "",
                    "description": "Test description",
                    "hdnDiscountAmount": "0.00000000",
                    "hdnDiscountPercent": "0.000",
                    "hdnSubTotal": "0.00000000",
                    "hdnGrandTotal": "0.00000000",
                    "pricebook_id": "",
                    "items_sync_with": "",
                    "hdnS_H_Percent": "",
                    "hdnS_H_Amount": "0.00000000",
                    "id": "5x495",
                    "record_currency_symbol": "₹",
                    "lineItems": [[]],
                }
            ],
        }

        if crm_vtiger_dict.get("success"):
            crm_result = crm_vtiger_dict.get("result")[0]

            # Create User
            if crm_result.get("assigned_user_id"):
                self.env["res.users"].create(
                    {
                        "name": "Test user",
                        "login": "test@test",
                        "mobile": 6669998883,
                        "vtiger_id": crm_result.get("assigned_user_id"),
                    }
                )

            # Create Partner
            if crm_result.get("contact_id"):
                self.env["res.partner"].create(
                    {
                        "name": "Test partner",
                        "mobile": 6669998883,
                        "street": "Sector 1",
                        "vtiger_id": crm_result.get("contact_id"),
                    }
                )

            # Create Lead
            self.env["crm.lead"].create(
                {
                    "name": crm_result.get("potentialname"),
                    "email_from": crm_result.get("email"),
                    "date_deadline": crm_result.get("closingdate"),
                    "expected_revenue": crm_result.get("forecast_amount"),
                    "description": crm_result.get("description"),
                    "activity_summary": crm_result.get("nextstep"),
                    "priority": crm_result.get("starred", ""),
                    "vtiger_id": crm_result.get("id"),
                }
            )
