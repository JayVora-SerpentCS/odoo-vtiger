# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
