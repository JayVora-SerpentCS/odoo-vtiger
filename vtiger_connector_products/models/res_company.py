# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, models

import json
import urllib
import urllib2


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_products()

    @api.multi
    def sync_vtiger_products(self):
        for company in self:
            self.sync_vtiger_service_products()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Products
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Products;"""
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
                product_templ_obj = self.env['product.template']
#                partner_obj = self.env['res.partner']
                for res in result.get('result', []):
                    product_vals = {
                        'name': res.get('productname', ''),
                        'sale_ok': True,
                        'purchase_ok': True,
                        'type': 'consu',
                        'default_code': res.get('serial_no'),
                        'list_price': res.get('unit_price'),
                        'standard_price': res.get('purchase_cost'),
                        'description_sale': res.get('description')}
#                        'description': res.get('description'),
#                        'title_action': res.get('nextstep'),
#                        'priority': res.get('starred', ''),
#                        'source_id': res.get('source'),
#                        'stage_id': res.get('sales_stage'),
#                    contact_id = res.get('contact_id')
#                    if contact_id:
#                        partner = partner_obj.search(
#                            [('vtiger_id', '=', contact_id)], limit=1
#                        )
#                        if partner:
#                            crm_vals.update({'partner_id': partner.id})
                    # Search for existing partner
                    product = product_templ_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if product:
                        product.write(product_vals)
                    else:
                        product_vals.update({'vtiger_id': res.get('id')})
                        product_templ_obj.create(product_vals)
        return True

    @api.multi
    def sync_vtiger_service_products(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Services
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Services;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urllib.urlencode(values)
            url = company.get_vtiger_server_url()
            req = urllib2.Request("%s?%s" % (url, data))
            response = urllib2.urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                product_templ_obj = self.env['product.template']
                for res in result.get('result', []):
                    product_vals = {
                        'name': res.get('servicename', ''),
                        'sale_ok': True,
                        'purchase_ok': True,
                        'type': 'service',
                        'default_code': res.get('serial_no'),
                        'list_price': res.get('unit_price'),
                        'standard_price': res.get('purchase_cost'),
                        'description_sale': res.get('description'),
                    }
                    product = product_templ_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if product:
                        product.write(product_vals)
                    else:
                        product_vals.update({'vtiger_id': res.get('id')})
                        product_templ_obj.create(product_vals)
        return True
