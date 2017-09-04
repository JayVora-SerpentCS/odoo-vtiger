# -*- coding: utf-8 -*-
from odoo import api, models

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
            where = ''
            if company.last_sync_date:
                where = " WHERE modifiedtime >= %s " % (company.last_sync_date)
            qry = "SELECT * FROM Contacts %s;" % (where)
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
                partner_obj = self.env['res.partner']
                country_obj = self.env['res.country']
                for res in result.get('result', []):
                    partner_vals = {
                        'name': res.get('firstname', '') + ' ' +
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
