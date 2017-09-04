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
        return self.sync_vtiger_event()

    @api.multi
    def sync_vtiger_event(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            where = ''
            if company.last_sync_date:
                where = " WHERE modifiedtime >= %s " % (company.last_sync_date)
            qry = "SELECT * FROM Events %s;" % (where)
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
                event_obj = self.env['calendar.event']
                partner_obj = self.env['res.partner']
                for res in result.get('result', []):
                    event_vals = {
                        'name': res.get('subject', ''),
                        'description': res.get('description'),
                        'privacy': res.get('visibility', '') == 'Public' and
                            'public' or (res.get('visibility', '') == 'Private'
                                         and 'private' or ''),
                        'start_date': res.get('date_start'),
                        'stop_date': res.get('due_date'),
                        'recurrency': bool(res.get('recurringtype', '')),
                        'rrule_type': res.get('recurringtype', '').lower(),
                    }
                    contact_id = res.get('contact_id')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1
                        )
                        if partner:
                            event_vals.update({'partner_id': partner.id})
                    # Search for existing Event
                    event = event_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if event:
                        event.write(event_vals)
                    else:
                        event_vals.update({'vtiger_id': res.get('id')})
                        event_obj.create(event_vals)
        return True
