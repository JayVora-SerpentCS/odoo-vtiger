# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models

import json
import urllib
import urllib2


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_partner()

    @api.multi
    def sync_vtiger_partner(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            values = {
                'operation': 'query',
                'query': 'SELECT * FROM Contacts;',
                'sessionName': session_name,
            }
            data = urllib.urlencode(values)
            url = company.get_vtiger_server_url()
            req = urllib2.Request("%s?%s" % (url, data))
            response = urllib2.urlopen(req)
            print '\n\nabout Contacts'
            result = json.loads(response.read())
#{u'mailingstreet': u'7105 Plover Circle, Fort Worth Texas', u'othercountry': u'',
#u'reference': u'0', u'mailingcity': u'Houston', u'mailing_gps_lat': u'0.0000000', u'salutationtype': u'Mr.',
#u'support_start_date': u'2013-11-15', u'contact_id': u'', u'happiness_rating': u'',
#u'emailoptout': u'0', u'leadsource': u'Cold Call', u'secondaryemail': u'', u'last_contacted_via': u''
#u'support_end_date': u'2014-11-15', u'otherstate': u'', u'slaid': u'', u'profile_score': u'',
#u'assistantphone': u'', u'otherzip': u'', u'id': u'4x42', u'account_id': u'3x32', u'mailingzip': u'',
#u'record_currency_symbol': None, u'modifiedtime': u'2017-08-10 11:17:49', u'title': u'VP Operations',
#u'othercity': u'', u'source': u'WEBSERVICE', u'mailing_gps_lng': u'0.0000000', u'lastname': u'Alexander',
#u'department': u'', u'donotcall': u'0', u'otherphone': u'', u'email': u'Jacob@jaallc-vt.com',
#u'last_contacted_on': u'', u'otherstreet': u'', u'birthday': u'1978-09-21', u'fax': u'324234232',
#u'record_currency_id': u'', u'description': u'', u'firstname': u'Jacob', u'tags': u'',
#u'assistant': u'', u'engagement_score': u'0', u'contacttype': u'Lead', u'otherpobox': u'',
#u'contact_no': u'CON1', u'phone': u'1-934-343-7398', u'isconvertedfromlead': u'1',
#u'portal': u'0', u'assigned_user_id': u'19x1', u'referred_by': u'', u'createdtime': u'2017-08-10 11:17:49',
#u'mailingstate': u'Texas', u'contactstatus': u'', u'mailingpobox': u'1289', u'created_user_id': u'19x1',
#u'primary_twitter': u'', u'mobile': u'1-(456)-456-6745', u'imagename': u'', u'notify_owner': u'0',
#u'modifiedby': u'19x1', u'starred': u'0', u'profile_rating': u'', u'mailingcountry': u'USA', u'homephone': u'',
#u'record_conversion_rate': u''}
            if result.get('success'):
                partner_obj = self.env['res.partner']
                country_obj = self.env['res.country']
                for res in result.get('result', []):
                    partner_vals = {
                        'name': res.get('firstname', '') + ' ' +\
                            res.get('lastname', ''),
                        'email': res.get('email'),
                        'supplier': res.get('contacttype') == 'Vendor'
                            and True,
                        'street': res.get('mailingstreet'),
                        'city': res.get('mailingcity'),
                        'zip': res.get('mailingzip'),
                        'opt_out': res.get('emailoptout', False),
                        'mobile': res.get('mobile'),
                        'phone': res.get('phone'),
                        'fax': res.get('fax'),
                        'comment': res.get('description'),
                    }
                    mailingcountry = res.get('mailingcountry')
                    if mailingcountry:
                        country = country_obj.search(
                            ['|', ('name', '=', mailingcountry),
                             ('code', '=', mailingcountry)], limit=1
                        )
                        if country:
                            partner_vals.update({'country_id': country.id})
                    # Search for existing partner
                    partner = partner_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if partner:
                        partner.write(partner_vals)
                    else:
                        partner_vals.update({'vtiger_id': res.get('id')})
                        partner_obj.create(partner_vals)
        return True
