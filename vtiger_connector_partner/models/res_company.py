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
        return self.sync_vtiger_partner()

    @api.multi
    def sync_vtiger_partner(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Contacts
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Contacts;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                partner_obj = self.env['res.partner']
                country_obj = self.env['res.country']
                for res in result.get('result', []):
                    partner_vals = {
                        'name': res.get('firstname', '') + ' ' +
                        res.get('lastname', ''),
                        'email': res.get('email'),
                        'customer': True,
                        'street': res.get('mailingstreet'),
                        'city': res.get('mailingcity'),
                        'zip': res.get('mailingzip'),
                        'opt_out': res.get('emailoptout', False),
                        'mobile': res.get('mobile'),
                        'phone': res.get('phone'),
                        'comment': res.get('description')}
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
            self.sync_vtiger_partner_vendor()
            self.sync_vtiger_partner_organizations()
        return True

    @api.multi
    def sync_vtiger_partner_vendor(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Vendors
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Vendors;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                partner_obj = self.env['res.partner']
                country_obj = self.env['res.country']
                for res in result.get('result', []):
                    partner_vals = {
                        'name': res.get('vendorname'),
                        'email': res.get('email'),
                        'website': res.get('website'),
                        'supplier': True,
                        'street': res.get('street'),
                        'city': res.get('city'),
                        'zip': res.get('postalcode'),
                        'mobile': res.get('mobile'),
                        'phone': res.get('phone'),
                        'comment': res.get('description'),
                        'ref': res.get('vendor_no')
                    }
                    mailingcountry = res.get('country')
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

    @api.multi
    def sync_vtiger_partner_organizations(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            if company.last_sync_date:
                qry = ("""SELECT * FROM Accounts
                            WHERE modifiedtime >= '%s';"""
                       % (company.last_sync_date))
            else:
                qry = """SELECT * FROM Accounts;"""
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request("%s?%s" % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                partner_obj = self.env['res.partner']
                country_obj = self.env['res.country']
                for res in result.get('result', []):
                    partner_vals = {
                        'name': res.get('accountname'),
                        'email': res.get('email1'),
                        'website': res.get('website'),
                        'supplier': True,
                        'customer': True,
                        'street': res.get('bill_street'),
                        'city': res.get('bill_city'),
                        'zip': res.get('bill_code'),
                        'phone': res.get('phone'),
                        'comment': res.get('description')}
#                    TODO need to develop for users
                    rec_country = res.get('bill_country')
                    if rec_country:
                        country = country_obj.search(
                            ['|', ('name', '=', rec_country),
                             ('code', '=', rec_country)], limit=1
                        )
                        if country:
                            partner_vals.update({'country_id': country.id})
                    # Search for existing partner
                    partner = partner_obj.search([
                        ('vtiger_id', '=', res.get('id')),
                        ('is_company', '=', 'True')], limit=1)
                    if partner:
                        partner.write(partner_vals)
                    else:
                        partner_vals.update({
                            'vtiger_id': res.get('id'),
                            'is_company': True
                        })
                        partner_obj.create(partner_vals)
        return True
