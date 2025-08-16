from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerSales(TransactionCase):
    def test_vtiger_sales(self):
        vtiger_sales_dict = {
            "success": True,
            "result": [
                {
                    "subject": "SO test 1",
                    "potential_id": "",
                    "quote_id": "",
                    "vtiger_purchaseorder": "1111",
                    "contact_id": "4x494",
                    "customerno": "",
                    "account_id": "",
                    "pending": "",
                    "sostatus": "New",
                    "duedate": "2024-10-10",
                    "hdnSubTotal": "50.00000000",
                    "assigned_user_id": "19x1",
                    "hdnGrandTotal": "56.00000000",
                    "carrier": "",
                    "salescommission": "",
                    "exciseduty": "",
                    "hdnTaxType": "group",
                    "createdtime": "2024-10-01 09:13:51",
                    "modifiedtime": "2024-10-01 09:13:51",
                    "salesorder_no": "SO7",
                    "currency_id": "21x2",
                    "conversion_rate": "1.00000",
                    "modifiedby": "19x1",
                    "pre_tax_total": "50.00000000",
                    "created_user_id": "19x1",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "isclosed": "0",
                    "signature": "",
                    "orderdate": "2024-10-01",
                    "gst_in": "",
                    "enable_recurring": "0",
                    "recurring_frequency": "",
                    "start_period": "",
                    "end_period": "",
                    "payment_duration": "",
                    "invoicestatus": "",
                    "ship_country": "",
                    "bill_country": "AU",
                    "bill_street": "Billing Address SO",
                    "ship_street": "Shipping Address SO",
                    "bill_pobox": "Billing PO Box",
                    "ship_pobox": "Shipping PO Box",
                    "bill_city": "Billing city",
                    "ship_city": "Shipping City",
                    "bill_state": "Australian Capital Territory",
                    "ship_state": "Australian Capital Territory",
                    "bill_code": "1111111",
                    "ship_code": "333333",
                    "hdnDiscountAmount": "",
                    "hdnDiscountPercent": "0.000",
                    "hdnS_H_Percent": "0",
                    "txtAdjustment": "0.00000000",
                    "hdnS_H_Amount": "0.00000000",
                    "region_id": "1",
                    "pricebook_id": "",
                    "purchase_cost_total": "0.00000000",
                    "margin_total": "50.00000000",
                    "margin_percentage_total": "100.00000000",
                    "markup_percentage_total": "0.00000000",
                    "terms_conditions": "- Unless otherwise agreed in writing by the "
                    "supplier all invoices are payable within "
                    "thirty (30) days of the date of invoice, "
                    "in the currency of the invoice, drawn on "
                    "a bank based in India or by such other "
                    "method as is agreed in advance by the "
                    "Supplier",
                    "description": "THIS IS SO DESCRIPTION",
                    "id": "15x506",
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
                            "purchase_cost": "0.00000000",
                            "margin": "50.00000000",
                            "netprice": "50.00000000",
                            "section_no": "1",
                            "section_name": "",
                            "margin_percentage": "100.00",
                            "delivered_qty": "0.000",
                            "outstanding_qty": "1.000",
                            "markup_percentage": "100.00",
                            "duration": "1.00000000",
                            "billing_type": "One time",
                            "unit_purchase_cost": "0.00000000",
                            "overall_item_discount": "0.00000000",
                            "discounted_unit_selling_price": "50.00000000",
                            "tax4": "6.00000",
                            "tax5": "6.00000",
                            "tax6": "0.00000",
                        }
                    ],
                }
            ],
        }

        if vtiger_sales_dict.get("success"):
            so_result = vtiger_sales_dict.get("result")[0]
            so_line_result = so_result.get("lineItems")[0]

            # Create the vendor
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

            # Create the sale order
            so_rec = self.env["sale.order"].create(
                {
                    "partner_id": partner_rec.id,
                    "state": "draft",
                    "date_order": so_result.get("duedate"),
                    "vtiger_id": so_result.get("id"),
                }
            )

            # Create the sale order line
            self.env["sale.order.line"].create(
                {
                    "name": so_line_result.get("comment"),
                    "product_id": 1,
                    "product_uom_qty": float(so_line_result.get("quantity") or 0.00),
                    "price_unit": float(so_line_result.get("listprice") or 0.00),
                    "price_subtotal": float(so_line_result.get("netprice") or 0.00),
                    "order_id": so_rec.id,
                }
            )

            so_rec.sudo().action_confirm()
