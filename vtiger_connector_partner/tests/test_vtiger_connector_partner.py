from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerPartner(TransactionCase):
    def test_vtiger_partner(self):
        # Sample Partner data
        vtiger_partner_dict = {
            "success": True,
            "result": [
                {
                    "salutationtype": "Mr.",
                    "firstname": "contact",
                    "lastname": "contact",
                    "email": "contact@contact.com",
                    "phone": "+91852852",
                    "mobile": "",
                    "homephone": "",
                    "birthday": "2000-09-19",
                    "otherphone": "",
                    "fax": "",
                    "account_id": "",
                    "title": "",
                    "department": "",
                    "contact_id": "",
                    "leadsource": "",
                    "secondaryemail": "",
                    "assistant": "",
                    "assigned_user_id": "19x1",
                    "assistantphone": "",
                    "donotcall": "0",
                    "notify_owner": "0",
                    "emailoptout": "0",
                    "createdtime": "2024-09-27 11:52:24",
                    "modifiedtime": "2024-09-27 11:52:24",
                    "contact_no": "CON24",
                    "modifiedby": "19x1",
                    "isconvertedfromlead": "0",
                    "created_user_id": "19x1",
                    "primary_twitter": "",
                    "source": "CRM",
                    "engagement_score": "0",
                    "last_contacted_on": "",
                    "last_contacted_via": "",
                    "slaid": "",
                    "starred": "0",
                    "tags": "",
                    "contacttype": "Lead",
                    "contactstatus": "Cold",
                    "happiness_rating": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "profile_score": "0",
                    "profile_rating": "0",
                    "referred_by": "",
                    "emailoptin": "singleoptinuser",
                    "emailoptin_requestcount": "0",
                    "emailoptin_lastrequestedon": "",
                    "smsoptin": "singleoptinuser",
                    "language": "",
                    "primary_phone_field": "",
                    "primary_email_field": "",
                    "isclosed": "0",
                    "source_campaign": "",
                    "platform": "",
                    "adgroup": "",
                    "facebook_lead_id": "",
                    "portal": "0",
                    "support_start_date": "2024-09-27",
                    "support_end_date": "2025-09-27",
                    "mailingcountry": "AU",
                    "othercountry": "",
                    "mailingstreet": "Mailing Street",
                    "otherstreet": "",
                    "mailingpobox": "Mailing PO Box",
                    "otherpobox": "",
                    "mailingcity": "Mailing City",
                    "othercity": "",
                    "mailingstate": "Australian Capital Territory",
                    "otherstate": "",
                    "mailingzip": "zip 11111",
                    "otherzip": "",
                    "mailing_gps_lat": "",
                    "mailing_gps_lng": "",
                    "description": "Contact Description",
                    "imagename": "",
                    "consent_requested": "0",
                    "consent_trash_data": "",
                    "data_erased": "0",
                    "consent_lock_data": "",
                    "consent_track_email_engagement": "",
                    "consent_track_shared_documents": "",
                    "consents_last_requested_on": "",
                    "primary_linkedin": "",
                    "followers_linkedin": "",
                    "primary_facebook": "",
                    "followers_facebook": "",
                    "facebookid": "0",
                    "instagramid": "",
                    "twitterid": "",
                    "id": "4x498",
                    "record_currency_symbol": None,
                }
            ],
        }

        if vtiger_partner_dict.get("success"):
            partner_result = vtiger_partner_dict.get("result")[0]

            # Create Partner
            self.env["res.partner"].create(
                {
                    "name": partner_result.get("salutationtype")
                    + partner_result.get("firstname")
                    + partner_result.get("lastname"),
                    "email": partner_result.get("email"),
                    "phone": partner_result.get("phone"),
                    "mobile": partner_result.get("mobile"),
                    "street": partner_result.get("mailingstreet"),
                    "city": partner_result.get("mailingcity"),
                    "zip": partner_result.get("zip"),
                    "vtiger_id": partner_result.get("id"),
                }
            )

        # Sample Vendor data
        vtiger_vendor_dict = {
            "success": True,
            "result": [
                {
                    "vendorname": "Test vendor",
                    "phone": "+916666666666",
                    "email": "vendor@vendor.com",
                    "website": "",
                    "glacct": "",
                    "category": "",
                    "createdtime": "2024-09-27 12:21:57",
                    "modifiedtime": "2024-09-27 12:21:57",
                    "vendor_no": "VEN12",
                    "modifiedby": "19x1",
                    "assigned_user_id": "19x1",
                    "created_user_id": "19x1",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "primary_phone_field": "",
                    "primary_email_field": "",
                    "country": "AU",
                    "street": "Street 1",
                    "pobox": "vedor po box",
                    "city": "Vendor City",
                    "state": "Australian Capital Territory",
                    "postalcode": "",
                    "description": "Vendor Description Details",
                    "id": "11x499",
                    "isclosed": "0",
                    "record_currency_symbol": None,
                }
            ],
        }

        if vtiger_vendor_dict.get("success"):
            vendor_result = vtiger_vendor_dict.get("result")[0]

            self.env["res.partner"].create(
                {
                    "name": vendor_result.get("vendorname"),
                    "email": vendor_result.get("email"),
                    "phone": vendor_result.get("phone"),
                    "street": vendor_result.get("street"),
                    "city": vendor_result.get("city"),
                    "zip": vendor_result.get("zip"),
                    "supplier_rank": 1,
                    "vtiger_id": vendor_result.get("id"),
                }
            )

        # Sample Account data
        vtiger_account_dict = {
            "success": True,
            "result": [
                {
                    "accountname": "Test Account",
                    "email1": "account@account.com",
                    "website": "",
                    "otherphone": "",
                    "email2": "",
                    "phone": "+915252525263",
                    "employees": "",
                    "industry": "",
                    "annual_revenue": "",
                    "annual_revenue_currency_value": "",
                    "fax": "",
                    "account_id": "",
                    "ownership": "",
                    "accounttype": "Lead",
                    "tickersymbol": "",
                    "assigned_user_id": "19x1",
                    "notify_owner": "0",
                    "emailoptout": "0",
                    "siccode": "",
                    "account_no": "ACC14",
                    "createdtime": "2024-09-27 12:26:56",
                    "modifiedtime": "2024-09-27 12:26:56",
                    "modifiedby": "19x1",
                    "isconvertedfromlead": "0",
                    "created_user_id": "19x1",
                    "primary_twitter": "",
                    "source": "CRM",
                    "last_contacted_on": "",
                    "last_contacted_via": "",
                    "slaid": "",
                    "starred": "0",
                    "tags": "",
                    "email_domain": "",
                    "accountstatus": "Cold",
                    "record_currency_id": "21x2",
                    "record_conversion_rate": "1.00000",
                    "region": "",
                    "profile_score": "0",
                    "profile_rating": "0",
                    "emailoptin": "singleoptinuser",
                    "emailoptin_requestcount": "0",
                    "emailoptin_lastrequestedon": "",
                    "smsoptin": "singleoptinuser",
                    "primary_phone_field": "",
                    "primary_email_field": "",
                    "isclosed": "0",
                    "gst_in": "",
                    "ship_country": "AU",
                    "bill_country": "",
                    "bill_street": "Account Billing Address",
                    "ship_street": "",
                    "bill_pobox": "Account PO Box",
                    "ship_pobox": "",
                    "bill_city": "Account City",
                    "ship_city": "",
                    "bill_state": "Australian Capital Territory",
                    "ship_state": "",
                    "bill_code": "4574",
                    "ship_code": "",
                    "mailing_gps_lat": "",
                    "mailing_gps_lng": "",
                    "description": "Account Description Details",
                    "imagename": "",
                    "id": "3x500",
                    "record_currency_symbol": "₹",
                }
            ],
        }

        if vtiger_account_dict.get("success"):
            account_result = vtiger_account_dict.get("result")[0]

            self.env["res.partner"].create(
                {
                    "name": account_result.get("accountname"),
                    "email": account_result.get("email1"),
                    "phone": account_result.get("phone"),
                    "mobile": account_result.get("mobile"),
                    "supplier_rank": 1,
                    "customer_rank": 1,
                    "street": account_result.get("bill_street"),
                    "city": account_result.get("bill_city"),
                    "zip": account_result.get("bill_code"),
                    "comment": account_result.get("description"),
                    "vtiger_id": account_result.get("id"),
                }
            )
