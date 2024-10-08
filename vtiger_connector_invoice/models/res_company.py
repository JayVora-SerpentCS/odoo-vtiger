# See LICENSE file for full copyright and licensing details.

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_invoice()

    def delete_existing_invoice(self, result):
        """Added the Method for the Work Existing invoice line,
        Because the Vtiger return dictionary"""
        invoice_obj = self.env["account.move"]
        for res in result.get("result", []):
            invoice_id = invoice_obj.search(
                [("vtiger_id", "=", res.get("id"))], limit=1
            )
            if invoice_id and invoice_id.state == "draft":
                # invoice_id.invoice_line_ids.unlink() # while sync data it gives
                # Cannot create unbalanced journal entry. Ids: [18] Differences
                # debit - credit: [500.0] error.

                # 2024-07-01 12:16:58,158 40186 WARNING 16_vtiger_intergation
                # odoo.http: You cannot delete a tax line as it would impact the
                # tax report
                invoice_id and invoice_id.invoice_line_ids.unlink()
        return True

    def _build_query_invoice(self, company):
        """Build query based on the last sync date."""
        if company.last_sync_date:
            return """SELECT * FROM Invoice WHERE modifiedtime >= '%s';""" % (
                company.last_sync_date
            )
        return """SELECT * FROM Invoice;"""

    def _execute_vtiger_query_invoice(self, company, qry, session_name):
        """Execute the query on VTiger."""
        values = {"operation": "query", "query": qry, "sessionName": session_name}
        data = urlencode(values)
        url = company.get_vtiger_server_url()
        req = Request("%s?%s" % (url, data))
        response = urlopen(req, timeout=20)
        return json.loads(response.read())

    def _get_partner(self, res, company):
        """sync partner data."""
        partner_obj = self.env["res.partner"]
        if res.get("contact_id"):
            partner = partner_obj.search(
                [("vtiger_id", "=", res.get("contact_id"))], limit=1
            )
            if not partner:
                company.sync_vtiger_partner()
                partner = partner_obj.search(
                    [("vtiger_id", "=", res.get("contact_id"))], limit=1
                )
            return partner

    def _sync_invoice_lines(self, res, invoice_id, company):
        """Sync invoice lines."""
        product_obj = self.env["product.product"]
        account_payment_register_obj = self.env["account.payment.register"]
        res.get("hdnGrandTotal")
        for order_line_dict in res.get("lineItems"):
            if type(order_line_dict) != dict:
                order_line_dict = res.get("lineItems").get(order_line_dict)
            product = order_line_dict.get("productid")
            if product:
                product = product_obj.search([("vtiger_id", "=", product)], limit=1)
                if not product:
                    company.sync_vtiger_products(
                        company, vtiger_type=["Products", "Services"]
                    )
            accounts = product.product_tmpl_id.get_product_accounts()
            price_unit = order_line_dict.get("listprice")
            quantity = order_line_dict.get("quantity")

            invoice_line_vals = {
                "name": order_line_dict.get("description"),
                "product_id": product and product.id,
                "product_uom_id": product.uom_id.id,
                "quantity": float(quantity or 0.00),
                "price_unit": float(price_unit or 0.00),
                "move_id": invoice_id.id,
                "account_id": accounts["income"].id,
            }
            if res.get("invoicestatus") == "Credit Invoice":
                invoice_id.type = "out_refund"
            if not invoice_id.state == "posted":
                invoice_id.write({"invoice_line_ids": [(0, 0, invoice_line_vals)]})
            if res.get("invoicestatus") in ["Created", "Sent"]:
                invoice_id.state = "draft"
            elif res.get("invoicestatus") == "Paid":
                invoice_id.action_post()
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
                account_payment_register_rec = (
                    account_payment_register_obj.with_context(
                        active_model="account.move",
                        active_ids=[invoice_id.id],
                    ).create(
                        {
                            "journal_id": journal_id,
                            "amount": invoice_id.amount_total,
                            "payment_date": invoice_id.invoice_date,
                            "communication": invoice_id.name,
                        }
                    )
                )
                account_payment_register_rec.action_create_payments()

    def sync_vtiger_invoice(self):
        invoice_obj = self.env["account.move"]
        partner_obj = self.env["res.partner"]
        user_obj = self.env["res.users"]
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = self._build_query_invoice(company)
            result = self._execute_vtiger_query_invoice(company, qry, session_name)
            if result.get("success"):
                self.delete_existing_invoice(result)

                for res in result.get("result", []):
                    self._get_partner(res, company)
                    invoice_vals = {}
                    invoice_id = invoice_obj.search(
                        [("vtiger_id", "=", res.get("id"))], limit=1
                    )
                    if not invoice_id:
                        contact_id = res.get("contact_id")
                        if contact_id:
                            partner = partner_obj.search(
                                [("vtiger_id", "=", contact_id)], limit=1
                            )
                            if partner:
                                invoice_vals.update({"partner_id": partner.id})
                        else:
                            vtiger_user = user_obj.search(
                                [("login", "=", "vtigeruser@vtiger")]
                            )
                            if not vtiger_user:
                                vtiger_user = user_obj.create(
                                    {
                                        "name": "VTiger-User",
                                        "login": "vtigeruser@vtiger",
                                    }
                                )
                            invoice_vals.update(
                                {"partner_id": vtiger_user.partner_id.id}
                            )
                        date_invoice = res.get("invoicedate")
                        if date_invoice:
                            invoice_vals.update({"invoice_date": date_invoice})
                        date_due = res.get("duedate")
                        if date_due:
                            invoice_vals.update({"invoice_date_due": date_due})
                        invoice_vals.update(
                            {
                                "vtiger_id": res.get("id"),
                                "move_type": "out_invoice",
                                "narration": res.get("terms_conditions"),
                            }
                        ),
                        invoice_id = invoice_obj.create(invoice_vals)

                    self._sync_invoice_lines(res, invoice_id, company)
        return True
