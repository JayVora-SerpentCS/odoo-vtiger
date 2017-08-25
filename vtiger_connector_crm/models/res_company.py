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
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            values = {
                'operation': 'query',
                'query': 'SELECT * FROM Potentials;',
                'sessionName': session_name,
            }
            data = urllib.urlencode(values)
            url = company.get_vtiger_server_url()
            req = urllib2.Request("%s?%s" % (url, data))
            response = urllib2.urlopen(req)
            print '\n\nabout Potentials'
            result = json.loads(response.read())
            print "\n##    ", result.get('success')

#            {u'potentialname': u'Alienware 14 Notebook - 100 Pcs', u'forecast_category': u'Closed',
#u'probability': u'100.000', u'related_to': u'3x40', u'contact_id': u'4x46',
#u'leadsource': u'Conference', u'modifiedby': u'19x1', u'last_contacted_via': u'',
#u'created_user_id': u'19x1', u'closingdate': u'2014-02-06', u'id': u'5x62',
#u'record_currency_symbol': u'$', u'modifiedtime': u'2017-08-10 11:17:50',
#u'amount_currency_value': u'239000.00000000', u'opportunity_type': u'Existing Business',
#u'adjusted_amount_currency_value': u'239000.00000000', u'email': u'',
#u'last_contacted_on': u'', u'record_currency_id': u'21x1',
#u'description': u'Opportunity to sell 100 Alienware 14 Notebooks',
#u'prev_sales_stage': u'', u'tags': u'', u'isconvertedfromlead': u'0',
#u'potential_no': u'POT1', u'assigned_user_id': u'19x1', u'createdtime': u'2017-08-10 11:17:50',
#u'forecast_amount': u'239000.00000000', u'current_stage_entry_time': u'2017-08-10 11:17:50',
#u'adjusted_amount': u'239000.00000000', u'campaignid': u'', u'nextstep': u'Already Contacted',
#u'amount': u'239000.00000000', u'source': u'WEBSERVICE', u'sales_stage': u'Closed Won',
#u'starred': u'0', u'lost_reason': u'', u'forecast_amount_currency_value': u'239000.00000000',
#u'record_conversion_rate': u'1.00000'}
            if result.get('success'):
                print "\n\n#@@@@@@@@@@@%%%    ", result.get('result')
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
