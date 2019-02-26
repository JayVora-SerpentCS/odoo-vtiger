from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
