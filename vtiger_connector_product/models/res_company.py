# -*- coding: utf-8 -*-
from odoo import api, models

import json
import urllib
import urllib2

PRODUCT_TYPES = ['Products', 'Services']


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_product()

    @api.multi
    def sync_vtiger_product(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            where = ''
            if company.last_sync_date:
                where = " WHERE modifiedtime >= %s " % (company.last_sync_date)
            for product_type in PRODUCT_TYPES:
                qry = "SELECT * FROM %s %s;" % (product_type, where)
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
                    product_obj = self.env['product.product']
                    for res in result.get('result', []):
                        product_vals = {
#                        'barcode': res.get('serial_no'),
                            'lst_price': res.get('unit_price'),
                            'description_sale': res.get('description'),
                            'standard_price': res.get('purchase_cost'),
                        }
                        if product_type == 'Products':
                            product_vals.update({
                                'name': res.get('productname', ''),
                                'type': 'product',
                                'default_code': res.get('productcode'),
#                                'uom_id': '', # usageunit
                            })
                        else:
                            product_vals.update({
                                'name': res.get('servicename', ''),
                                'type': 'service',
                                'default_code': res.get('service_no'),
#                                'uom_id': '', # service_usageunit
                            })
                        # Search for existing Product
                        product = product_obj.search(
                            [('vtiger_id', '=', res.get('id'))], limit=1
                        )
                        if product:
                            product.write(product_vals)
                        else:
                            product_vals.update({'vtiger_id': res.get('id')})
                            product_obj.create(product_vals)
        return True
