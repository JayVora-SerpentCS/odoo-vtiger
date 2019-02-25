# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, date

import json
import urllib
import urllib2


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_purchase_order()

    @api.multi
    def sync_vtiger_purchase_order(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            # Synchronise Product
            company.sync_vtiger_products()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = """SELECT * FROM PurchaseOrder WHERE modifiedtime >= '%s';""" % (company.last_sync_date)
            values = {
                'operation': 'query',
                'query': qry,
                'sessionName': session_name,
            }
            data = urllib.urlencode(values)
            url = company.get_vtiger_server_url()
            req = urllib2.Request("%s?%s" % (url, data))
            response = urllib2.urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                purchase_order_obj = self.env['purchase.order']
                purchase_line_obj = self.env['purchase.order.line']
                partner_obj = self.env['res.partner']
                product_obj = self.env['product.product']
                for res in result.get('result', []):
#                    purchase order
                    order_vals = {
                        'notes': res.get('terms_conditions'),
                    }
#                    purchase order line
                    price_unit = res.get('listprice')
                    netprice = res.get('netprice')
                    quantity = res.get('quantity')
                    order_line_vals = {
                        'name': res.get('comment'),
                        'product_qty': float(quantity),
                        'price_unit': float(price_unit),
                        'price_subtotal': float(netprice)
                    }
#                    changing the date format of createdtime
                    date_o = res.get('createdtime')
                    if date_o:
                        awe = str(date_o)
                        date_frm = datetime.strptime(awe, '%Y-%m-%d %H:%M:%S')
                        date_order = date_frm.strftime('%d-%m-%Y')
                        order_vals.update({'date_order': date_order})
                        order_line_vals.update({'date_planned': date_order})
                    date_modified = res.get('modifiedtime')
                    if date_modified:
                        modified = str(date_modified)
                        modified_date = datetime.strptime(modified, '%Y-%m-%d %H:%M:%S')
                        date_planned = modified_date.strftime('%d-%m-%Y')
                        order_vals.update({'date_planned': date_planned})
                        order_line_vals.update({'date_planned': date_planned})
#                    for order line values
                    product_id = res.get('productid')
                    if product_id:
                        product = product_obj.search(
                            [('vtiger_id', '=', product_id)], limit=1
                        )
                        if product:
                            if product.uom_po_id:
                                order_line_vals.update({'product_uom': product.uom_po_id.id})
                            else:
                                order_line_vals.update({'product_uom': product.uom_id.id})
                            order_line_vals.update({'product_id': product.id})
                    contact_id = res.get('vendor_id')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1
                        )
                        if partner:
                            order_vals.update({'partner_id': partner.id})
                    # Search for existing sale order
                    purchase_order = purchase_order_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if purchase_order:
                        line_ids = purchase_line_obj.search([('order_id', '=', purchase_order.id)])
                        if line_ids:
                            line_ids.unlink()
                        order_vals.update({'order_line': [(0, 0, order_line_vals)]})
                        purchase_order.write(order_vals)
                    else:
                        order_vals.update({'vtiger_id': res.get('id')})
                        order_vals.update({'order_line': [(0, 0, order_line_vals)]})
                        purchase_order_obj.create(order_vals)
                    
        return True
