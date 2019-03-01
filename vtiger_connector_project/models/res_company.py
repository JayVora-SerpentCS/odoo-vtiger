# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import json
from odoo import api, models
from urllib.request import urlopen, Request
from urllib.parse import urlencode


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_project()

    @api.multi
    def sync_vtiger_project(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Project
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Project;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                project_obj = self.env['project.project']
                partner_obj = self.env['res.partner']
                for res in result.get('result', []):
                    project_vals = {
                        'name': res.get('projectname'),
                    }
                    contact_id = res.get('linktoaccountscontacts')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1)
                        if partner:
                            project_vals.update({'partner_id': partner.id})
                    # Search for existing partner
                    crm = project_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1)
                    if crm:
                        crm.write(project_vals)
                    else:
                        project_vals.update({'vtiger_id': res.get('id')})
                        project_obj.create(project_vals)
        return True
