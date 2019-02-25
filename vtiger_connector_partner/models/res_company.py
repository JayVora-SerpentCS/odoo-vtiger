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
        return self.sync_vtiger_partner()

    @api.multi
    def sync_vtiger_partner(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            print "access_key-----10---------", access_key
            session_name = company.vtiger_login(access_key)
            qry = """SELECT * FROM Contacts WHERE modifiedtime >= '%s';""" % (company.last_sync_date)
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
                        'name': res.get('firstname', '') + ' ' +\
                            res.get('lastname', ''),
                        'email': res.get('email'),
                        'customer': True,
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
            self.sync_vtiger_partner_vendor()
            self.sync_vtiger_partner_organizations()
        return True

    @api.multi
    def sync_vtiger_partner_vendor(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = """SELECT * FROM Vendors WHERE modifiedtime >= '%s';""" % (company.last_sync_date)
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
                        'name': res.get('vendorname'),
                        'email': res.get('email'),
                        'website': res.get('website'),
                        'supplier': True,
                        'street': res.get('street'),
                        'city': res.get('city'),
                        'zip': res.get('postalcode'),
                        'mobile': res.get('mobile'),
                        'phone': res.get('phone'),
                        'fax': res.get('fax'),
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
            qry = """SELECT * FROM Accounts WHERE modifiedtime >= '%s';""" % (company.last_sync_date)
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
                        'name': res.get('accountname'),
                        'email': res.get('email1'),
                        'website': res.get('website'),
                        'supplier': True,
                        'customer': True,
                        'street': res.get('bill_street'),
                        'city': res.get('bill_city'),
                        'zip': res.get('bill_code'),
                        'phone': res.get('phone'),
                        'fax': res.get('fax'),
                        'comment': res.get('description'),
                    }
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
                    partner = partner_obj.search([('vtiger_id', '=', res.get('id')), ('is_company', '=', 'True')], limit=1)
                    if partner:
                        partner.write(partner_vals)
                    else:
                        partner_vals.update({
                            'vtiger_id': res.get('id'),
                            'is_company': True
                        })
                        partner_obj.create(partner_vals)
        return True