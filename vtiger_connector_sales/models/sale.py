# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
import json
import requests


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vtiger_id = fields.Char('VTiger ID', readonly=True)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for rec in self:
            rec.create_vtiger_record()
        return res

    @api.multi
    def create_vtiger_record(self):
        company = self.env.user.company_id
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        vtiger_admin_id = company.vtiger_admin_id
        url = company.get_vtiger_server_url()
        for rec in self:
            line_id_records = []
            for line_id in rec.order_line:
                line_res = {
                    'productid': str(line_id.product_id.vtiger_id),
                    'comment': str(line_id.product_id.name),
                    'quantity': line_id.product_uom_qty or 1,
                    'outstanding_qty': line_id.product_uom_qty or 1,
                    'listprice': line_id.price_unit or 1,
                    'delivered_qty': 0,
                    'netprice': line_id.price_subtotal or 0,
                    'region_id': 1,
                }
                line_id_records.append(line_res)
            json_datas = {
                'salesorder_no': str(rec.name) or "New",
                'subject': str(rec.name) or "New",
                'contact_id': str(rec.partner_id.vtiger_id),
                'sostatus': 'New',
                'assigned_user_id': vtiger_admin_id,
                'source': 'Odoo',
                'createdtime': str(rec.date_order) or '',
                'duedate': str(rec.validity_date) or '',
                'bill_street': str(rec.partner_id.street) or "Billing",
                'ship_street': str(rec.partner_id.street) or "Shipping",
                'terms_conditions': str(rec.note),
                'section_name': 'Order Lines',
                'hdnTaxType': 'individual',
                'hdnDiscountPercent': 0.0,
                'region_id': 1,
                'LineItems': line_id_records,
                }
            values = {'operation': 'create',
                      'sessionName': session_name,
                      'element': json.dumps(json_datas),
                      'elementType': "SalesOrder",
                      }
            resp = requests.post(url=url, data=values).json()
            if 'result' in resp:
                if 'success' in resp and resp.get('success') is True:
                    result = resp.get('result')
                    if 'id' in result and result.get('id', False):
                        rec.vtiger_id = result.get('id')
        return True

