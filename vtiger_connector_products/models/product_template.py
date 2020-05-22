# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
