# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from datetime import datetime
from six.moves.urllib.request import urlopen, Request
from six.moves.urllib.parse import urlencode


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_purchase_order()

    @api.multi
    def update_existing_order(self, result):
        '''Added the Method for the Work Existing order line,
           Because the Vtiger return dictionary'''
        purchase_order_obj = self.env['purchase.order']
        for res in result.get('result', []):
            order_id = purchase_order_obj.search(
                [('vtiger_id', '=', res.get('id'))], limit=1)
            if order_id:
                order_id.order_line.unlink()
        return True

    @api.multi
    def sync_vtiger_purchase_order(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            # Synchronise Product
            company.sync_vtiger_products()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM PurchaseOrder
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM PurchaseOrder;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            purchase_order_obj = self.env['purchase.order']
            partner_obj = self.env['res.partner']
            product_obj = self.env['product.product']
            if result.get('success'):
                self.update_existing_order(result)
                for res in result.get('result', []):
                    order_id = purchase_order_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1)
                    po_order_vals = {}
                    if not order_id:
                        contact_id = res.get('vendor_id')
                        if contact_id:
                            partner = partner_obj.search(
                                [('vtiger_id', '=', contact_id)], limit=1)
                            if partner:
                                po_order_vals.update(
                                    {'partner_id': partner.id})
                        date_o = res.get('createdtime')
                        if date_o:
                            awe = str(date_o)
                            date_frm = datetime.strptime(awe, DT)
                            date_order = date_frm.strftime(DT)
                            po_order_vals.update({'date_order': date_order})
                        date_modified = res.get('modifiedtime')
                        if date_modified:
                            modified = str(date_modified)
                            modified_date = datetime.strptime(modified, DT)
                            date_planned = modified_date.strftime(DF)
                            po_order_vals.update(
                                {'date_planned': date_planned})
                        po_order_vals.update(
                            {'vtiger_id': res.get('id'),
                             'notes': res.get('terms_conditions')}),
                        order_id = purchase_order_obj.create(po_order_vals)
                    product_id = res.get('productid')
                    if product_id:
                        product = product_obj.search(
                            [('vtiger_id', '=', product_id)], limit=1)
                    price_unit = res.get('listprice')
                    netprice = res.get('hdnGrandTotal')
                    quantity = res.get('quantity')
                    order_line_vals = {
                        'name': res.get('comment'),
                        'product_id': product and product.id or False,
                        'product_uom': product.uom_id.id,
                        'product_qty': float(quantity),
                        'price_unit': float(price_unit),
                        'price_subtotal': float(netprice),
                        'order_id': order_id.id,
                        'date_planned': order_id.date_order}
                    if order_id:
                        order_id.write(
                            {'order_line': [(0, 0, order_line_vals)]})
        return True
