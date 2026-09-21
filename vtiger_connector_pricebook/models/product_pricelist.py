# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    vtiger_id = fields.Char("VTiger ID", readonly=True, copy=False, index=True)
    vtiger_active = fields.Boolean("VTiger Active", readonly=True)
    vtiger_description = fields.Text("VTiger Description", readonly=True)
