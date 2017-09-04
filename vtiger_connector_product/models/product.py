# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
