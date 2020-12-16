# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
from odoo import api, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DT
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import urlencode
import requests
from requests.auth import HTTPBasicAuth


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_sale_order()

    @api.multi
    def update_existing_sale_order(self, result):
        '''Added the Method for the Work Existing order line,
           Because the Vtiger return dictionary'''
        sale_order_obj = self.env['sale.order']
        for res in result.get('result', []):
            order_id = sale_order_obj.search(
                [('vtiger_id', '=', res.get('id'))], limit=1)
            if order_id:
                order_id.order_line.unlink()
        return True

    @api.multi
    def sync_vtiger_sale_order(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            # Synchronise Product
            company.sync_vtiger_products()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM SalesOrder
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM SalesOrder;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            sale_order_obj = self.env['sale.order']
            partner_obj = self.env['res.partner']
            lead_obj = self.env['crm.lead']
            product_obj = self.env['product.product']
            if result.get('success'):
                self.update_existing_sale_order(result)
                for res in result.get('result', []):
                    so_id = res.get('id')
                    line_url = company.vtiger_server
                    line_url += "/restapi/v1/vtiger/default/retrieve?id=" + so_id
                    line_req = requests.get(line_url, auth=(
                        company.user_name, company.access_key))
                    line_req_json = line_req.json()
                    order_id = sale_order_obj.search(
                        [('vtiger_id', '=', so_id)], limit=1)
                    so_order_vals = {}
                    if not order_id:
                        contact_id = line_req_json['result']['contact_id']
                        if contact_id:
                            partner = partner_obj.search(
                                [('vtiger_id', '=', contact_id)], limit=1)
                            if partner:
                                so_order_vals.update(
                                    {'partner_id': partner.id})
                        date_o = line_req_json['result']['createdtime']
                        if date_o:
                            awe = str(date_o)
                            date_frm = datetime.strptime(awe, DT)
                            date_order = date_frm.strftime(DT)
                            so_order_vals.update(
                                {'date_order': date_order,
                                 'confirmation_date': date_order})
                        date_due = line_req_json['result']['duedate']
                        if date_due:
                            dat_due = str(date_due)
                            date_format = datetime.strptime(dat_due, DF)
                            so_order_vals.update(
                                {'validity_date': date_format})
                        opportunity_id = line_req_json[
                            'result']['potential_id']
                        if opportunity_id:
                            opportunity = lead_obj.search(
                                [('vtiger_id', '=', opportunity_id)], limit=1)
                            if opportunity:
                                so_order_vals.update(
                                    {'opportunity_id': opportunity.id})
                        so_order_vals.update(
                            {'vtiger_id': line_req_json['result']['id'],
                             'note': line_req_json['result']['terms_conditions']}),
                        order_id = sale_order_obj.create(so_order_vals)
                    order_line = []
                    for line in line_req_json['result']['LineItems']:
                        product_id = line.get('productid')
                        if product_id:
                            product = product_obj.search(
                                [('vtiger_id', '=', product_id)], limit=1)
                        price_unit = line.get('listprice')
                        netprice = line.get('netprice')
                        quantity = line.get('quantity')
                        order_line_vals = {
                            'name': line.get('comment'),
                            'product_id': product and product.id or False,
                            'product_uom': product.uom_id.id,
                            'product_uom_qty': float(quantity),
                            'price_unit': float(price_unit),
                            'price_subtotal': float(netprice),
                            'order_id': order_id.id}
                        order_line.append((0, 0, order_line_vals))
                    if order_id:
                        order_id.write({
                            'order_line': order_line})
                    if res.get('sostatus') == 'Approved':
                        order_id.sudo().action_confirm()
            company.sync_vtiger_sale_Quotes()
        return True

    @api.multi
    def sync_vtiger_sale_Quotes(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Quotes
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Quotes;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            sale_order_obj = self.env['sale.order']
            partner_obj = self.env['res.partner']
            lead_obj = self.env['crm.lead']
            product_obj = self.env['product.product']
            if result.get('success'):
                self.update_existing_sale_order(result)
                for res in result.get('result', []):
                    if res.get('quotestage') == 'New':
                        so_id = res.get('id')
                        line_url = company.vtiger_server
                        line_url += "/restapi/v1/vtiger/default/retrieve?id=" + so_id
                        line_req = requests.get(line_url, auth=(
                            company.user_name, company.access_key))
                        line_req_json = line_req.json()
                        order_id = sale_order_obj.search(
                            [('vtiger_id', '=', so_id)], limit=1)
                        so_order_vals = {}
                        if not order_id:
                            contact_id = line_req_json['result']['contact_id']
                            if contact_id:
                                partner = partner_obj.search(
                                    [('vtiger_id', '=', contact_id)], limit=1)
                                if partner:
                                    so_order_vals.update(
                                        {'partner_id': partner.id})
                            date_o = line_req_json['result']['createdtime']
                            if date_o:
                                awe = str(date_o)
                                date_frm = datetime.strptime(awe, DT)
                                date_order = date_frm.strftime(DT)
                                so_order_vals.update(
                                    {'date_order': date_order,
                                     'confirmation_date': date_order})
                            date_due = line_req_json['result']['validtill']
                            if date_due:
                                dat_due = str(date_due)
                                date_format = datetime.strptime(dat_due, DF)
                                so_order_vals.update(
                                    {'validity_date': date_format})
                            opportunity_id = line_req_json[
                                'result']['potential_id']
                            if opportunity_id:
                                opportunity = lead_obj.search(
                                    [('vtiger_id', '=', opportunity_id)],
                                    limit=1)
                                if opportunity:
                                    so_order_vals.update(
                                        {'opportunity_id': opportunity.id})
                            so_order_vals.update(
                                {'vtiger_id': line_req_json['result']['id'],
                                 'note': line_req_json['result']['terms_conditions'],
                                 'state': 'draft', }),
                            order_id = sale_order_obj.create(so_order_vals)

                        order_line = []
                        for line in line_req_json['result']['LineItems']:
                            product_id = line.get('productid')
                            if product_id:
                                product = product_obj.search(
                                    [('vtiger_id', '=', product_id)], limit=1)
                            price_unit = line.get('listprice')
                            netprice = line.get('netprice')
                            quantity = line.get('quantity')
                            order_line_vals = {
                                'name': line.get('comment'),
                                'product_id': product and product.id or False,
                                'product_uom': product.uom_id.id,
                                'product_uom_qty': float(quantity),
                                'price_unit': float(price_unit),
                                'price_subtotal': float(netprice),
                                'order_id': order_id.id}
                            order_line.append((0, 0, order_line_vals))
                        if order_id:
                            order_id.write({'order_line': order_line})
        return True
