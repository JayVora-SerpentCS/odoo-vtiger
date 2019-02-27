# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import json
import requests
from hashlib import md5
from datetime import datetime
from urllib.request import urlopen
from urllib.parse import urlencode

URL = 'webservice.php'


class ResCompany(models.Model):
    _inherit = 'res.company'

    access_key = fields.Char('Access Key')
    vtiger_server = fields.Char('VTiger Server')
    user_name = fields.Char('User Name')
    last_sync_date = fields.Datetime('Last Synced Time')

    @api.multi
    def get_vtiger_server_url(self):
        return '%s/%s' % (self.vtiger_server, URL)

    @api.multi
    def get_vtiger_access_key(self):
        """Get the token using 'getchallenge' operation"""
        self.ensure_one()
        values = {'operation': 'getchallenge', 'username': self.user_name}
        data = urlencode(values)
        url = self.get_vtiger_server_url()
        req = urlopen('%s?%s' % (url, data))
        response = req.read()
        token = json.loads(response)['result']['token']
        # Use the TOKEN + ACCESSKEY to create the tokenized accessKey
        tokenized_accessKey = md5(token.encode('utf-8') +
                                  self.access_key.encode('utf-8'))
        return tokenized_accessKey.hexdigest()

    @api.multi
    def vtiger_login(self, access_key):
        """Using AccessKey tokenized, perform a login operation."""
        self.ensure_one()
        values = {'operation': 'login',
                  'username': self.user_name,
                  'accessKey': access_key}
        url = self.get_vtiger_server_url()
        response = requests.post(url=url, data=values).json()
        # Return sessionName
        return response['result']['sessionName']

    @api.model
    def sync_vtiger(self):
        return self.search([]).action_sync_vtiger()

    @api.multi
    def action_sync_vtiger(self):
        self.write({'last_sync_date': datetime.now()})
        return True
