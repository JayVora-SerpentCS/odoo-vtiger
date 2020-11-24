# See LICENSE file for full copyright and licensing details.

import json

from odoo import api, models
from urllib.request import urlopen, Request
from urllib.parse import urlencode


class ResCompany(models.Model):
    _inherit = 'res.company'

    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_crm()

    def sync_vtiger_crm(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Potentials
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Potentials;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                crm_obj = self.env['crm.lead']
                partner_obj = self.env['res.partner']
                for res in result.get('result', []):
                    crm_vals = {
                        'name': res.get('potentialname', ''),
                        'email_from': res.get('email'),
                        'probability': float(res.get('probability')) or 0.0,
                        'date_deadline': res.get('closingdate'),
                        'expected_revenue': res.get('forecast_amount'),
                        'description': res.get('description'),
                        'activity_summary': res.get('nextstep'),
                        'priority': res.get('starred', '')}
                    contact_id = res.get('contact_id')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1
                        )
                        if partner:
                            crm_vals.update({'partner_id': partner.id})
                    # Search for existing partner
                    crm = crm_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if crm:
                        crm.write(crm_vals)
                    else:
                        crm_vals.update({'vtiger_id': res.get('id')})
                        crm_obj.create(crm_vals)
        return True
