import json
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from datetime import datetime
from urllib.request import urlopen
from urllib.request import Request
from urllib.parse import urlencode


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def action_sync_vtiger(self):
        super(ResCompany, self).action_sync_vtiger()
        return self.sync_vtiger_sale_order()

    @api.multi
    def sync_vtiger_sale_order(self):
        for company in self:
            # Synchronise Partner
            company.sync_vtiger_partner()
            # Synchronise Product
            company.sync_vtiger_products()
            # Synchronise CRM
            company.sync_vtiger_crm()
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = ("""SELECT * FROM SalesOrder WHERE modifiedtime >= '%s';"""
                   % (company.last_sync_date))
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                sale_order_obj = self.env['sale.order']
                order_line_obj = self.env['sale.order.line']
                partner_obj = self.env['res.partner']
                lead_obj = self.env['crm.lead']
                product_obj = self.env['product.product']
#                order_line_obj = self.env['product.product']
                for res in result.get('result', []):
                    order_vals = {
                        'note': res.get('terms_conditions')}
#                    setting the stage
#                     quotestage = res.get('quotestage')
                    date_o = res.get('createdtime')
                    if date_o:
                        awe = str(date_o)
                        date_frm = datetime.strptime(awe, '%Y-%m-%d %H:%M:%S')
                        date_order = date_frm.strftime(DF)
                        order_vals.update({'date_order': date_order,
                                           'confirmation_date': date_order})
                    date_due = res.get('duedate')
                    if date_due:
                        dat_due = str(date_due)
                        date_format = datetime.strptime(dat_due, DF)
                        order_vals.update({'validity_date': date_format})
#                    for order line values
                    price_unit = res.get('listprice')
                    netprice = res.get('hdnGrandTotal')
                    quantity = res.get('quantity')
                    order_line_vals = {
                        'name': res.get('comment'),
                        'product_uom_qty': float(quantity),
                        'price_unit': float(price_unit),
                        'price_subtotal': float(netprice),
                    }
                    product_id = res.get('productid')
                    if product_id:
                        product = product_obj.search(
                            [('vtiger_id', '=', product_id)], limit=1
                        )
                        if product:
                            order_line_vals.update({'product_id': product.id})
                    contact_id = res.get('contact_id')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1
                        )
                        if partner:
                            order_vals.update({'partner_id': partner.id})
#                   linking opertunity with sale order
                    opportunity_id = res.get('potential_id')
                    if opportunity_id:
                        opportunity = lead_obj.search(
                            [('vtiger_id', '=', opportunity_id)], limit=1)
                        if opportunity:
                            order_vals.update({'opportunity_id':
                                               opportunity.id})
                    # Search for existing sale order
                    sale_order = sale_order_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if sale_order:
                        previous_state = str(sale_order.state)
                        sale_order.write({'state': 'draft'})
                        line_ids = order_line_obj.search(
                            [('order_id', '=', sale_order.id)]
                        )
                        if line_ids:
                            line_ids.unlink()
                        order_vals.update({
                            'order_line': [(0, 0, order_line_vals)],
                            'state': previous_state
                        })
                        sale_order.write(order_vals)
                    else:
                        order_vals.update({
                            'vtiger_id': res.get('id'),
                            'state': 'sale',
                            'order_line': [(0, 0, order_line_vals)]
                        })
                        sale_order_obj.create(order_vals)
        self.sync_vtiger_sale_Quotes()
        return True

#    for quotations of sales
    @api.multi
    def sync_vtiger_sale_Quotes(self):
        for company in self:
            access_key = company.get_vtiger_access_key()
            session_name = company.vtiger_login(access_key)
            qry = ("""SELECT * FROM Quotes WHERE modifiedtime >= '%s';"""
                   % (company.last_sync_date))
            values = {'operation': 'query',
                      'query': qry,
                      'sessionName': session_name}
            data = urlencode(values)
            url = company.get_vtiger_server_url()
            req = Request('%s?%s' % (url, data))
            response = urlopen(req)
            result = json.loads(response.read())
            if result.get('success'):
                sale_order_obj = self.env['sale.order']
                order_line_obj = self.env['sale.order.line']
                partner_obj = self.env['res.partner']
                lead_obj = self.env['crm.lead']
                product_obj = self.env['product.product']
#                order_line_obj = self.env['product.product']
                for res in result.get('result', []):
                    order_vals = {'note': res.get('terms_conditions')}
#                    setting the stage
                    date_o = res.get('createdtime')
                    if date_o:
                        awe = str(date_o)
                        date_frm = datetime.strptime(awe, '%Y-%m-%d %H:%M:%S')
                        date_order = date_frm.strftime(DF)
                        order_vals.update({'date_order': date_order})
#                    for order line values
                    price_unit = res.get('listprice')
                    netprice = res.get('hdnGrandTotal')
                    quantity = res.get('quantity')
                    order_line_vals = {
                        'name': res.get('comment'),
                        'product_uom_qty': float(quantity),
                        'price_unit': float(price_unit),
                        'price_subtotal': float(netprice),
                    }
                    product_id = res.get('productid')
                    if product_id:
                        product = product_obj.search(
                            [('vtiger_id', '=', product_id)], limit=1
                        )
                        if product:
                            order_line_vals.update({'product_id': product.id})
                    contact_id = res.get('contact_id')
                    if contact_id:
                        partner = partner_obj.search(
                            [('vtiger_id', '=', contact_id)], limit=1
                        )
                        if partner:
                            order_vals.update({'partner_id': partner.id})
#                   linking opertunity with sale order
                    opportunity_id = res.get('potential_id')
                    if opportunity_id:
                        opportunity = lead_obj.search(
                            [('vtiger_id', '=', opportunity_id)], limit=1
                        )
                        if opportunity:
                            order_vals.update(
                                {'opportunity_id': opportunity.id})
                    # Search for existing sale order
                    sale_order = sale_order_obj.search(
                        [('vtiger_id', '=', res.get('id'))], limit=1
                    )
                    if sale_order:
                        previous_state = str(sale_order.state)
                        sale_order.write({'state': 'draft'})
                        line_ids = order_line_obj.search(
                            [('order_id', '=', sale_order.id)]
                        )
                        if line_ids:
                            line_ids.unlink()
                        order_vals.update({
                            'order_line': [(0, 0, order_line_vals)],
                            'state': previous_state})
                        sale_order.write(order_vals)
                    else:
                        order_vals.update({
                            'vtiger_id': res.get('id'),
                            'state': 'draft',
                            'order_line': [(0, 0, order_line_vals)]})
                        sale_order_obj.create(order_vals)
        return True
