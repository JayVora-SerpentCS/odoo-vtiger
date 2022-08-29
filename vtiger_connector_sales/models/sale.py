# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models
import json
import requests
from six.moves.urllib.parse import urlencode
from six.moves.urllib.request import urlopen, Request
from six.moves.urllib.parse import urlencode


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vtiger_id = fields.Char('VTiger ID', readonly=True)

    def action_confirm(self):
        sale_order = super(SaleOrder, self).action_confirm()
        company = self.env.user.company_id
        access_key = company.get_vtiger_access_key()
        session_name = company.vtiger_login(access_key)
        print ("\nsession_name---------------------", session_name)
        qry = ("""INSERT INTO SalesOrder (subject, contact_id, sostatus, bill_street, ship_street) VALUES ('My Test', %s, 'Approved', %s, %s)"""
                       % (self.partner_id.id, self.partner_id.street, self.partner_id.street))
        values = {'operation': 'create',
                  'element': qry,
                  'elementType': 'SalesOrder',
                  'sessionName': session_name}
        data = urlencode(values)
        print ("\ndata=====================", data)
        url = company.get_vtiger_server_url()
        resp = requests.request("POST", '%s?%s' % (url, data), data=data)
        print ("\nresp---------------------------", resp)

        #req = Request('%s?%s' % (url, data))

        #response = urlopen(req)
        #result = json.loads(response.read())
        result = resp.json()
        print ("\nresult---------------------------", result)
