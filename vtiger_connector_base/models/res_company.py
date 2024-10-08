# See LICENSE file for full copyright and licensing details.

import json
from datetime import datetime
from hashlib import md5
from urllib.parse import urlencode
from urllib.request import urlopen

import requests

from odoo import api, fields, models

URL = "webservice.php"


class ResCompany(models.Model):
    _inherit = "res.company"

    access_key = fields.Char()
    vtiger_server = fields.Char()
    user_name = fields.Char()
    last_sync_date = fields.Datetime(string="Last Synced Time")

    def get_vtiger_server_url(self):
        return "%s/%s" % (self.vtiger_server, URL)

    def get_vtiger_access_key(self):
        """Get the token using 'getchallenge' operation"""
        self.ensure_one()
        values = {"operation": "getchallenge", "username": self.user_name}
        data = urlencode(values)
        url = self.get_vtiger_server_url()
        req = urlopen("%s?%s" % (url, data), timeout=20)
        response = req.read()
        token = json.loads(response)["result"]["token"]
        # Use the TOKEN + ACCESSKEY to create the tokenized accessKey
        tokenized_accessKey = md5(
            token.encode("utf-8") + self.access_key.encode("utf-8")
        )
        return tokenized_accessKey.hexdigest()

    def vtiger_login(self, access_key):
        """Using AccessKey tokenized, perform a login operation."""
        self.ensure_one()
        values = {
            "operation": "login",
            "username": self.user_name,
            "accessKey": access_key,
        }
        url = self.get_vtiger_server_url()
        response = requests.post(url=url, data=values, timeout=20).json()
        # Return sessionName
        return response["result"]["sessionName"]

    @api.model
    def sync_vtiger(self):
        return self.search([]).action_sync_vtiger()

    def action_sync_vtiger(self):
        self.write({"last_sync_date": datetime.now()})
        return True
