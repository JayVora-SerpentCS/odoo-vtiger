# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False)
    vtiger_record_type = fields.Char("VTiger Type", readonly=True, copy=False)
    vtiger_status = fields.Char("VTiger Status", readonly=True, copy=False)
