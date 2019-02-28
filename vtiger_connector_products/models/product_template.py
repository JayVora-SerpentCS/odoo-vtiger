# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    vtiger_id = fields.Char('VTiger ID', readonly=True)
