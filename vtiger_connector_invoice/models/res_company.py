# See LICENSE file for full copyright and licensing details.

import json
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from collections import defaultdict


class ResCompany(models.Model):
    _inherit = 'res.company'

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_invoice()

    def delete_existing_invoice(self, result):
        '''Added the Method for the Work Existing invoice line,
           Because the Vtiger return dictionary'''
        invoice_obj = self.env['account.move']
        for res in result.get('result', []):
            invoice_id = invoice_obj.search(
                [('vtiger_id', '=', res.get('id'))], limit=1)
            if invoice_id and invoice_id.state=='draft':
                invoice_id.invoice_line_ids.unlink()
        return True

    def sync_vtiger_invoice(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            # Synchronise Product
            company.sync_vtiger_products()
            #Get the access key for connection
            access_key = company.get_vtiger_access_key()
            #create session
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Invoice
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Invoice;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            invoice_obj = self.env['account.move']
            partner_obj = self.env['res.partner']
            product_obj = self.env['product.product']
            if result.get('success'):
                self.delete_existing_invoice(result)
                for res in result.get('result', []):
                    invoice_id = invoice_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1)
                    invoice_vals = {}
                    if not invoice_id:
                        contact_id = res.get('contact_id')
                        if contact_id:
                            partner = partner_obj.search(
                                [('vtiger_id', '=', contact_id)], limit=1)
                            if partner:
                                invoice_vals.update(
                                    {'partner_id': partner.id})
                        date_invoice = res.get('start_date')
                        if date_invoice:
                            awe = str(date_invoice)
                            date_frm = datetime.strptime(awe, DT)
                            date_order = date_frm.strftime(DT)
                            invoice_vals.update(
                                {'invoice_date': date_order})
                        date_due = res.get('expiry_date')
                        if date_due:
                            dat_due = str(date_due)
                            date_format = datetime.strptime(dat_due, DF)
                            invoice_vals.update(
                                {'invoice_date_due': date_format})
                        invoice_vals.update(
                            {'vtiger_id': res.get('id'),
                             'move_type':'out_invoice',
                             'narration': res.get('terms_conditions')}),
                        invoice_id = invoice_obj.create(invoice_vals)
                    product = res.get('productid')
                    if product:
                        product = product_obj.search(
                            [('vtiger_id', '=', product)], limit=1)
                    accounts = product.product_tmpl_id.get_product_accounts()
                    price_unit = res.get('listprice')
                    amount = res.get('hdnGrandTotal')
                    quantity = res.get('quantity')
                    invoice_line_vals = {
                        'name': res.get('description'),
                        'product_id': product and product.id or False,
                        'product_uom_id': product.uom_id.id,
                        'quantity': float(quantity),
                        'price_unit': float(price_unit),
                        'move_id': invoice_id.id,
                        'account_id':accounts['income']}
                    if res.get('invoicestatus')=="Credit Invoice":
                        invoice_id.type = 'out_refund'
                    if not invoice_id.state=='posted':
                        invoice_id.write({
                            'invoice_line_ids': [(0, 0, invoice_line_vals)]})
                    if res.get('invoicestatus') in ['Created','Sent']:
                        invoice_id.state='draft'
                    elif res.get('invoicestatus')=='Paid':
                        invoice_id.action_post()
                        payment_obj = self.env['account.payment']
                        data = [self._prepare_payment_vals(invoice_id, amount)]
                        payments = payment_obj.create(data)
                        payments.post()
        return True

    def _prepare_payment_vals(self, invoices, amount):
        '''Create the payment values.
        '''
        journal_id = self.env['account.journal'].search(
                        [('company_id', '=', self.env.company.id), 
                         ('type', 'in', ('bank', 'cash'))], 
                        limit=1).id
        payment_method_id = self.env['account.payment.method'].search([
                                ('payment_type', '=', 'inbound')], limit=1).id
        values = {
            'journal_id':journal_id,
            'payment_method_id': payment_method_id,
            'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices),
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': 'inbound',
            'amount': abs(float(amount)),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].partner_id.id,
            'partner_type': 'customer',
        }
        return values
