from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerPurchase(TransactionCase):
    def test_vtiger_purchase(self):
        vtiger_purchase_dict = {
            "success": True,
            "result": [
                {
                    "subject": "Test PO",
                    "vendor_id": "11x499",
                    "postatus": "New",
                    "requisition_no": "",
                    "contact_id": "4x494",
                    "duedate": "2024-10-10",
                    "hdnGrandTotal": "56.00000000",
                    "hdnTaxType": "group",
                    "salescommission": "",
                    "exciseduty": "",
                    "carrier": "",
                    "tracking_no": "",
                    "createdtime": "2024-10-01 05:35:27",
                    "hdnSubTotal": "50.00000000",
                    "modifiedtime": "2024-10-01 05:35:27",
                    "assigned_user_id": "19x1",
                    "purchaseorder_no": "PO7",
                    "currency_id": "21x2",
                    "conversion_rate": "1.00000",
                    "modifiedby": "19x1",
                    "pre_tax_total": "50.00000000",
                    "paid": "0.00000000",
                    "balance": "56.00000000",
                    "created_user_id": "19x1",
                    "accountid": "",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "salesorder_id": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "isclosed": "0",
                    "signature": "",
                    "orderdate": "2024-10-01",
                    "gst_in": "",
                    "bill_country": "",
                    "ship_country": "AU",
                    "bill_street": "test",
                    "ship_street": "Shipping address",
                    "bill_pobox": "Billing PO Box",
                    "ship_pobox": "Shipping PO Box",
                    "bill_city": "Billing City",
                    "ship_city": "Shipping City",
                    "bill_state": "Australian Capital Territory",
                    "ship_state": "Australian Capital Territory",
                    "bill_code": "",
                    "ship_code": "",
                    "terms_conditions": "- Unless otherwise agreed in writing by"
                    " the supplier all invoices are payable within"
                    " thirty (30) days of the date of invoice, in"
                    " the currency of the invoice, drawn on a bank"
                    " based in India or by such other method as is"
                    " agreed in advance by the Supplier.",
                    "hdnDiscountAmount": "",
                    "hdnDiscountPercent": "0.000",
                    "hdnS_H_Percent": "0",
                    "hdnS_H_Amount": "0.00000000",
                    "txtAdjustment": "0.00000000",
                    "region_id": "1",
                    "description": "This is PO description.",
                    "id": "14x505",
                    "record_currency_symbol": None,
                    "lineItems": [
                        {
                            "productid": "6x503",
                            "quantity": "1.000",
                            "listprice": "50.00000000",
                            "comment": "SEP TEST PRODUCT",
                            "tax1": "",
                            "tax2": "",
                            "tax3": "",
                            "image": "",
                            "netprice": "50.00000000",
                            "section_no": "1",
                            "section_name": "",
                            "outstanding_qty": "1.000",
                            "received_qty": "0.000",
                            "duration": "1.00000000",
                            "billing_type": "One time",
                            "overall_item_discount": "0.00000000",
                            "tax4": "6.00000",
                            "tax5": "6.00000",
                            "tax6": "0.00000",
                        }
                    ],
                }
            ],
        }

        if vtiger_purchase_dict.get("success"):
            po_result = vtiger_purchase_dict.get("result")[0]
            po_line_result = po_result.get("lineItems")[0]

            # Create the vendor (res.partner)
            partner_rec = self.env["res.partner"].create(
                {
                    "name": "Test Vendor",
                    "email": "test123@gmail.com",
                    "phone": 2225556664,
                    "street": "Test street",
                    "city": "Test city",
                    "zip": "858552",
                    "supplier_rank": 1,
                }
            )

            # Create the product
            self.env["product.template"].create(
                {
                    "name": "Test Product",
                    "detailed_type": "consu",
                    "purchase_line_warn": "no-message",
                }
            )

            # Create the purchase order
            po_rec = self.env["purchase.order"].create(
                {
                    "partner_id": partner_rec.id,
                    "state": "draft",
                    "date_order": po_result.get("duedate"),
                    "notes": po_result.get("terms_conditions"),
                    "vtiger_id": po_result.get("id"),
                }
            )

            # Create the purchase order line
            self.env["purchase.order.line"].create(
                {
                    "name": po_line_result.get("comment"),
                    "product_id": 1,
                    "product_qty": float(po_line_result.get("quantity") or 0.00),
                    "price_unit": float(po_line_result.get("listprice") or 0.00),
                    "price_subtotal": float(po_line_result.get("netprice") or 0.00),
                    "order_id": po_rec.id,
                    "date_planned": po_rec.date_order.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
