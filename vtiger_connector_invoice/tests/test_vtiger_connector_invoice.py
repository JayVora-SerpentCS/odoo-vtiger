from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("scs_custom_vtiger_test")
class TestVtigerInvoice(TransactionCase):
    def test_vtiger_invoice(self):
        vtiger_invoice_dict = {
            "success": True,
            "result": [
                {
                    "subject": "INVOICE TEST",
                    "account_id": "3x500",
                    "invoicedate": "2024-10-01",
                    "duedate": "2024-10-10",
                    "contact_id": "4x494",
                    "customerno": "",
                    "salesorder_id": "15x506",
                    "vtiger_purchaseorder": "",
                    "assigned_user_id": "19x1",
                    "invoicestatus": "Paid",
                    "salescommission": "",
                    "exciseduty": "",
                    "createdtime": "2024-10-01 10:04:22",
                    "hdnTaxType": "group",
                    "hdnGrandTotal": "56.00000000",
                    "hdnSubTotal": "50.00000000",
                    "modifiedtime": "2024-10-01 10:04:22",
                    "invoice_no": "INV6",
                    "currency_id": "21x2",
                    "conversion_rate": "1.00000",
                    "modifiedby": "19x1",
                    "pre_tax_total": "50.00000000",
                    "received": "0.00000000",
                    "balance": "56.00000000",
                    "created_user_id": "19x1",
                    "potential_id": "",
                    "source": "CRM",
                    "starred": "0",
                    "tags": "",
                    "projectid": "31x504",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "quote_id": "",
                    "applied_credits": "0.00000000",
                    "isclosed": "0",
                    "stockupdateapplied": "1",
                    "signature": "",
                    "gst_in": "",
                    "bill_country": "",
                    "ship_country": "AU",
                    "bill_street": "Account Billing Address",
                    "ship_street": "Shipping Address",
                    "bill_pobox": "Account PO Box",
                    "ship_pobox": "",
                    "bill_city": "Account City",
                    "ship_city": "",
                    "bill_state": "Australian Capital Territory",
                    "ship_state": "",
                    "bill_code": "4574",
                    "ship_code": "",
                    "terms_conditions": "- Unless otherwise agreed in writing by the "
                    "supplier all invoices are payable within "
                    "thirty (30) days of the date of invoice, "
                    "in the currency of the invoice, drawn on "
                    "a bank based in India or by such other "
                    "method as is agreed in advance by the"
                    " Supplier.",
                    "txtAdjustment": "0.00000000",
                    "hdnDiscountAmount": "",
                    "hdnDiscountPercent": "0.000",
                    "hdnS_H_Percent": "0.00000000",
                    "hdnS_H_Amount": "0.00000000",
                    "region_id": "1",
                    "pricebook_id": "",
                    "purchase_cost_total": "0.00000000",
                    "margin_total": "50.00000000",
                    "margin_percentage_total": "100.00000000",
                    "markup_percentage_total": "0.00000000",
                    "description": "This is invoice record.",
                    "id": "16x507",
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

        if vtiger_invoice_dict.get("success"):
            invoice_result = vtiger_invoice_dict.get("result")[0]
            invoice_line_result = invoice_result.get("lineItems")[0]

            # Create the vendor (partner)
            partner_rec = self.env["res.partner"].create(
                {
                    "name": "Test Vendor",
                    "email": "test123@gmail.com",
                    "phone": "2225556664",
                    "street": "Test street",
                    "city": "Test city",
                    "zip": "858552",
                    "supplier_rank": 1,
                }
            )

            # Create the product
            product_rec = self.env["product.product"].create(
                {
                    "name": "Test Product",
                    "detailed_type": "consu",
                    "purchase_line_warn": "no-message",
                }
            )
            accounts = product_rec.product_tmpl_id.get_product_accounts()

            # Create the invoice
            invoice_rec = self.env["account.move"].create(
                {
                    "partner_id": partner_rec.id,
                    "state": "draft",
                    "invoice_date": invoice_result.get("invoicedate"),
                    "invoice_date_due": invoice_result.get("duedate"),
                    "payment_reference": "Payment ref 001",
                    "vtiger_id": invoice_result.get("id"),
                    "amount_total": invoice_result.get("hdnGrandTotal"),
                }
            )

            # # Create the invoice line
            # self.env['account.move.line'].create({
            #     'name': invoice_line_result.get('comment'),
            #     'product_id': 1,
            #     'quantity': float(invoice_line_result.get('quantity') or 0.00),
            #     'price_unit': float(invoice_line_result.get('listprice') or 0.00),
            #     'price_subtotal': float(invoice_line_result.get('netprice') or 0.00),
            #     'move_id': invoice_rec.id,
            #     'account_id': accounts['income'].id,
            # })
            invoice_line_vals = {
                "name": invoice_line_result.get("comment"),
                "product_id": 1,
                "quantity": float(invoice_line_result.get("quantity") or 0.00),
                "price_unit": float(invoice_line_result.get("listprice") or 0.00),
                "price_subtotal": float(invoice_line_result.get("netprice") or 0.00),
                "move_id": invoice_rec.id,
                "account_id": accounts["income"].id,
            }

            invoice_rec.write({"invoice_line_ids": [(0, 0, invoice_line_vals)]})
            journal_id = (
                self.env["account.journal"]
                .search(
                    [
                        ("company_id", "=", self.env.company.id),
                        ("type", "in", ("bank", "cash")),
                    ],
                    limit=1,
                )
                .id
            )

            if invoice_result.get("invoicestatus") == "Paid":
                invoice_rec.action_post()
                self.env["account.payment.register"].with_context(
                    active_ids=[invoice_rec.id], active_model="account.move"
                ).create(
                    {
                        "journal_id": journal_id,
                        "amount": 500,
                        "payment_date": invoice_rec.invoice_date,
                        "communication": invoice_rec.name,
                    }
                ).action_create_payments()
