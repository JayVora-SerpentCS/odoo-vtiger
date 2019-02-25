# -*- coding: utf-8 -*-
from odoo import api, fields, models

import json
import urllib
import urllib2


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_crm()

    @api.multi
    def sync_vtiger_crm(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = """SELECT * FROM Potentials WHERE modifiedtime >= '%s';""" % (company.last_sync_date)
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
                crm_obj = self.env['crm.lead']
                partner_obj = self.env['res.partner']
                for res in result.get('result', []):
                    crm_vals = {
                        'name': res.get('potentialname', ''),
                        'email_from': res.get('email'),
                        'probability': res.get('probability'),
                        'date_deadline': res.get('closingdate'), # TODO: server format
                        'planned_revenue': res.get('forecast_amount'),
                        'description': res.get('description'),
                        'title_action': res.get('nextstep'),
                        'priority': res.get('starred', ''),
#                        'source_id': res.get('source'),
#                        'stage_id': res.get('sales_stage'),
                    }
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
